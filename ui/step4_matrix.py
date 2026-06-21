import streamlit as st

from core.brand_context_builder import BrandContextBuilder
from core.combination_engine import CombinationEngine
from core.llm_client import LLMClient
from core.models import ComboModel, ExcelRowModel
from core.prompt_builder import PromptBuilder
from core.session_manager import SessionManager
from rag.context_retriever import ContextRetriever

import uuid


def render(llm: LLMClient, retriever: ContextRetriever, sm: SessionManager) -> None:
    st.subheader("Step 4 — Generating Image Prompts")
    st.caption("Building all persona × hook combinations and crafting image prompts via the Art Director AI.")

    # Build brand context (once)
    if not sm.get("brand_context"):
        builder = BrandContextBuilder(llm)
        brief_model = builder.extract_brief_model(sm.get("client_brief", ""))
        sm.set("client_brief_model", brief_model)
        rag_ctx = sm.get("rag_context", "")
        brand_ctx = builder.build(brief_model, rag_ctx)
        sm.set("brand_context", brand_ctx)

    # Build combination matrix (once)
    if not sm.get("combo_matrix"):
        personas = sm.get("personas", [])
        hooks = sm.get("hooks", [])
        sel_p = set(sm.get("selected_persona_ids", []))
        sel_h = set(sm.get("selected_hook_ids", []))
        filtered_p = [p for p in personas if p.id in sel_p]
        filtered_h = [h for h in hooks if h.id in sel_h]
        engine = CombinationEngine()
        matrix = engine.build_matrix(filtered_p, filtered_h)
        sm.set("combo_matrix", matrix)

    combos: list[ComboModel] = sm.get("combo_matrix", [])
    prompt_sets = sm.get("prompt_sets", [])
    already_done = {ps.combo_id for ps in prompt_sets}
    pending = [c for c in combos if c.id not in already_done]

    if pending:
        brand_ctx = sm.get("brand_context", "")
        product_visual = sm.get("product_visual_context", "Not provided")
        builder = PromptBuilder(llm)

        total = len(combos)
        progress_bar = st.progress(len(prompt_sets) / total if total else 1.0, text="Building prompts...")
        status_text = st.empty()
        preview_container = st.container()

        for combo in pending:
            if sm.is_stop_requested():
                sm.clear_stop()
                st.warning("Stopped by user. Click 'Resume' to continue.")
                break

            rag_prompt_ctx = retriever.retrieve_similar_prompts(
                f"{combo.persona.name} {combo.hooks_text}"
            )
            ps = builder.build_for_combo(
                combo,
                brand_context=brand_ctx,
                product_visual=product_visual,
                rag_prompt_context=rag_prompt_ctx,
            )
            prompt_sets.append(ps)
            sm.set("prompt_sets", prompt_sets)
            done = len(prompt_sets)
            progress_bar.progress(done / total, text=f"Prompt {done}/{total}: {combo.persona.name}")
            status_text.caption(f"Hook: {combo.hooks_text[:60]}...")

            with preview_container.expander(
                f"{combo.persona.name} × {combo.hooks_text[:40]}...", expanded=False
            ):
                st.code(ps.prompt, language=None)

        # Build Excel rows from all prompt sets
        excel_rows = _build_excel_rows(combos, sm.get("prompt_sets", []), sm.get("client_name", ""))
        sm.set("excel_rows", excel_rows)

        if len(sm.get("prompt_sets", [])) == len(combos):
            st.success(f"All {len(prompt_sets)} prompts generated across {len(combos)} combinations.")

    else:
        st.success(f"All {len(prompt_sets)} prompts ready.")

    st.divider()
    col_back, col_next = st.columns([1, 1])
    if col_back.button("← Back"):
        sm.go_to_step(3)
        st.rerun()
    if col_next.button(
        "Export to Excel →",
        disabled=len(sm.get("prompt_sets", [])) < len(combos),
        type="primary",
    ):
        sm.advance_step()
        st.rerun()


def _build_excel_rows(
    combos: list[ComboModel],
    prompt_sets,
    client_name: str,
) -> list[ExcelRowModel]:
    ps_map = {ps.combo_id: ps for ps in prompt_sets}
    rows = []
    for combo in combos:
        ps = ps_map.get(combo.id)
        if not ps:
            continue
        hook_ids = ",".join(h.id for h in combo.hooks)
        hooks_display = " + ".join(h.name for h in combo.hooks)
        rows.append(ExcelRowModel(
            row_id=str(uuid.uuid4()),
            client_name=client_name,
            persona_id=combo.persona.id,
            persona_name=combo.persona.name,
            persona_description=combo.persona.description,
            hook_ids=hook_ids,
            hooks_text=hooks_display,
            prompt=ps.prompt,
            negative_prompt=ps.negative_prompt,
            creative_brief=ps.creative_brief,
            brand_name=ps.brand_name,
            dominant_palette=ps.dominant_palette,
            emotional_register=ps.emotional_register,
            composition_type=ps.composition_type,
            cta_zone=ps.cta_zone,
            brand_alignment=ps.brand_alignment,
            product_placement_zone=ps.product_placement_zone,
            select_flag=True,
        ))
    return rows


def _find_ps(prompt_sets, combo: ComboModel):
    for ps in prompt_sets:
        if ps.combo_id == combo.id:
            return ps
    return None
