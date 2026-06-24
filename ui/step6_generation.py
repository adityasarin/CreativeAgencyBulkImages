import threading
import time
from pathlib import Path

import streamlit as st

from core import generation_guard
from core.models import GenerationResultModel
from core.report_generator import ReportGenerator
from core.session_manager import SessionManager
from db import db_manager
from image_gen.batch_runner import BatchRunner
from image_gen.provider_factory import create_provider
from rag.campaign_indexer import CampaignIndexer
from rag.chroma_store import ChromaStore
from utils.file_utils import make_output_dir, make_run_dir, open_folder


def render(sm: SessionManager) -> None:
    st.subheader("Step 6 — Generating Images")

    filtered_rows = sm.get("filtered_rows", [])
    client_name = sm.get("client_name", "client")
    product_image = sm.get("product_image", None)

    # ── Orphaned job guard ────────────────────────────────────────────────────
    active_id = generation_guard.active_campaign_id()
    if active_id and active_id != sm.get("campaign_id"):
        st.error(
            "A previous image-generation job is still running in the background "
            f"(campaign `{active_id}`), likely left over from a 'Start Over' or a stop "
            "that didn't take effect. Starting a new job now would run two batches at "
            "once and double your API usage."
        )
        if st.button("Force-stop the orphaned job", type="primary"):
            generation_guard.stop_active()
            st.rerun()
        return

    # ── Start generation ──────────────────────────────────────────────────────
    if not sm.get("generation_running") and not sm.get("generation_complete"):
        already_done_ids = {r.row_id for r in sm.get("generation_results", []) if r.status == "success"}
        rows_to_process = [r for r in filtered_rows if r.row_id not in already_done_ids]

        if not rows_to_process:
            sm.set("generation_complete", True)
            st.rerun()
            return

        output_dir = sm.get("output_dir") or make_output_dir(client_name)
        run_dir = sm.get("run_dir") or make_run_dir(client_name)
        sm.set("output_dir", output_dir)
        sm.set("run_dir", run_dir)

        campaign_id = sm.get("campaign_id") or __import__("uuid").uuid4().hex
        sm.set("campaign_id", campaign_id)

        stop_event = generation_guard.try_start(campaign_id)
        if stop_event is None:
            st.error("Another generation job claimed the run slot just now. Please retry.")
            return
        sm.set("gen_stop_event", stop_event)

        try:
            db_manager.insert_campaign(
                campaign_id, client_name,
                sm.get("client_brief", "")[:500],
                len(sm.get("selected_persona_ids", [])),
                len(sm.get("selected_hook_ids", [])),
                create_provider().get_provider_name(),
                output_dir,
            )
        except Exception:
            pass

        sm.set("generation_running", True)
        sm.clear_stop()

        def _run():
            provider = create_provider()
            runner = BatchRunner(provider)
            lock: threading.Lock = sm.get("gen_lock")

            def on_result(result: GenerationResultModel):
                with lock:
                    current = st.session_state.get("generation_results", [])
                    current.append(result)
                    st.session_state["generation_results"] = current
                try:
                    db_manager.insert_result(campaign_id, result)
                except Exception:
                    pass

            try:
                results = runner.run(
                    rows=rows_to_process,
                    output_dir=output_dir,
                    progress_callback=on_result,
                    stop_check=lambda: stop_event.is_set() or sm.is_stop_requested(),
                    product_image=product_image,
                )
            finally:
                generation_guard.finish(campaign_id)
            st.session_state["generation_running"] = False
            st.session_state["generation_complete"] = not stop_event.is_set()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        st.rerun()

    # ── Live progress display ─────────────────────────────────────────────────
    if sm.get("generation_running") or sm.get("generation_complete"):
        results: list[GenerationResultModel] = sm.get("generation_results", [])
        n_total = len(filtered_rows)
        n_done = len([r for r in results if r.status in ("success", "failed")])
        n_success = len([r for r in results if r.status == "success"])
        n_failed = len([r for r in results if r.status == "failed"])

        if n_total > 0:
            st.progress(n_done / n_total, text=f"Generating... {n_done}/{n_total}")

        col_stats, col_preview = st.columns([2, 1])
        with col_stats:
            m1, m2, m3 = st.columns(3)
            m1.metric("Generated", n_success)
            m2.metric("Failed", n_failed)
            total_cost = sum(r.cost_usd for r in results)
            m3.metric("Cost so far", f"${total_cost:.2f}")

            # Scrolling log
            st.markdown("**Generation log:**")
            log_lines = []
            for r in results[-20:]:
                icon = "✅" if r.status == "success" else "❌"
                log_lines.append(
                    f"{icon} `{r.image_filename}` — {r.persona_name} / {r.hooks_text} "
                    f"({r.generation_time_sec:.1f}s)"
                )
            st.code("\n".join(log_lines) if log_lines else "Waiting for first image...", language=None)

        with col_preview:
            st.caption("Latest image")
            latest_ok = next((r for r in reversed(results) if r.status == "success"), None)
            if latest_ok and Path(latest_ok.image_path).exists():
                st.image(latest_ok.image_path, use_column_width=True)
                st.caption(f"{latest_ok.image_filename}")

        if sm.get("generation_running"):
            time.sleep(2)
            st.rerun()

    # ── Completion ────────────────────────────────────────────────────────────
    if sm.get("generation_complete"):
        results = sm.get("generation_results", [])
        n_success = len([r for r in results if r.status == "success"])
        st.success(f"Generation complete! **{n_success}** images saved.")
        st.balloons()

        # Build and show report
        if not sm.get("report_path"):
            gen = ReportGenerator()
            report_path = gen.generate(
                results,
                sm.get("run_dir", ""),
                client_name,
                feedback=sm.get("feedback", {}),
            )
            sm.set("report_path", report_path)

            # Update DB
            try:
                n_failed = len([r for r in results if r.status == "failed"])
                db_manager.update_campaign_stats(
                    sm.get("campaign_id", ""),
                    n_success, n_failed,
                    sum(r.cost_usd for r in results),
                    report_path,
                )
            except Exception:
                pass

            # Index to RAG
            try:
                store = ChromaStore()
                indexer = CampaignIndexer(store)
                indexer.index_campaign(
                    sm.get("client_brief", ""),
                    client_name,
                    results,
                )
                indexer.index_prompts(results)
            except Exception:
                pass

        report_path = sm.get("report_path", "")
        col_dl, col_folder, col_new = st.columns(3)

        if report_path and Path(report_path).exists():
            with open(report_path, "rb") as f:
                col_dl.download_button(
                    "⬇ Download Report",
                    data=f.read(),
                    file_name=Path(report_path).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        if col_folder.button("Open Output Folder"):
            open_folder(sm.get("output_dir", "."))

        if col_new.button("Start New Campaign", type="primary"):
            sm.reset()
            st.rerun()

    # ── Paused (stopped mid-run) ──────────────────────────────────────────────
    if not sm.get("generation_running") and not sm.get("generation_complete"):
        results = sm.get("generation_results", [])
        if results:
            st.warning(f"Generation paused. {len([r for r in results if r.status == 'success'])} images completed.")
            col_r, col_a = st.columns(2)
            if col_r.button("Resume Generation", type="primary"):
                sm.clear_stop()
                st.rerun()
            if col_a.button("Abandon & Export Partial Report"):
                sm.set("generation_complete", True)
                st.rerun()
