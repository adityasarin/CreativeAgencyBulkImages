import os

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from core import generation_guard
from core.llm_client import LLMClient
from core.session_manager import SessionManager
from db import db_manager
from rag.chroma_store import ChromaStore
from rag.context_retriever import ContextRetriever
from ui.step_router import render_current_step
from utils.file_utils import ensure_data_dir

st.set_page_config(
    page_title="BulkImageGen — Creative Agency",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bootstrap ─────────────────────────────────────────────────────────────────
ensure_data_dir()
db_manager.init_db()

sm = SessionManager()
sm.init()

llm = LLMClient()
store = ChromaStore()
retriever = ContextRetriever(store)

# ── Sidebar ───────────────────────────────────────────────────────────────────
STEP_LABELS = {
    1: "Brief",
    2: "Personas & Hooks",
    3: "Product Image",
    4: "Generate Prompts",
    5: "Review Excel",
    6: "Generate Images",
}

with st.sidebar:
    st.markdown("## 🎨 BulkImageGen")
    st.caption("AI-powered bulk ad image generation")
    st.divider()

    # Resume straight to image generation from a previously downloaded Excel
    generation_in_flight = generation_guard.active_campaign_id() is not None
    with st.expander("📂 Resume from Excel", expanded=False):
        st.caption("Already have a prompt spreadsheet from a past session? Upload it to jump straight to image generation.")
        resume_file = st.file_uploader(
            "Upload prompt spreadsheet",
            type=["xlsx"],
            key="resume_excel_upload",
            disabled=generation_in_flight,
        )
        if resume_file:
            from core.excel_manager import ExcelManager
            manager = ExcelManager()
            valid, error = manager.validate_schema(resume_file)
            if not valid:
                st.error(f"Invalid file: {error}")
            else:
                resume_file.seek(0)
                all_rows = manager.read_excel(resume_file)
                selected = [r for r in all_rows if r.select_flag]
                if not selected:
                    st.error("No rows are flagged select_flag=TRUE in this file.")
                else:
                    if st.button(f"Generate {len(selected)} images →", type="primary", key="resume_go"):
                        sm.reset()
                        sm.set("client_name", selected[0].client_name or "client")
                        sm.set("excel_rows", all_rows)
                        sm.set("filtered_rows", selected)
                        sm.go_to_step(6)
                        st.rerun()

    st.divider()

    # Step progress
    current = sm.get("current_step", 1)
    for step_n, label in STEP_LABELS.items():
        if step_n < current:
            st.markdown(f"✅ ~~Step {step_n}: {label}~~")
        elif step_n == current:
            st.markdown(f"**▶ Step {step_n}: {label}**")
        else:
            st.markdown(f"⬜ Step {step_n}: {label}")

    st.divider()

    # Stop button (active during generation)
    if sm.get("generation_running"):
        if st.button("⏹ Stop Generation", type="secondary", use_container_width=True):
            sm.request_stop()
            generation_guard.stop_active()
            st.rerun()

    # Feedback
    st.markdown("**Feedback**")
    feedback_text = st.text_area(
        "Notes for this step",
        key=f"sidebar_feedback_{current}",
        height=80,
        label_visibility="collapsed",
        placeholder="Leave feedback or notes here...",
    )
    if st.button("Submit Feedback", key=f"fb_btn_{current}"):
        if feedback_text.strip():
            sm.add_feedback(current, feedback_text.strip())
            st.success("Feedback saved.")

    st.divider()

    # Cost tracker
    results = sm.get("generation_results", [])
    if results:
        spent = sum(r.cost_usd for r in results)
        st.metric("Cost spent", f"${spent:.2f}")

    # Start over
    if generation_in_flight:
        st.caption("⚠️ Generation is running — stop it before starting over, or it will keep billing in the background.")
    if st.button("🔄 Start Over", use_container_width=True, disabled=generation_in_flight):
        sm.reset()
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
render_current_step(sm, llm, retriever)
