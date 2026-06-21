import streamlit as st

from core.combination_engine import CombinationEngine
from core.hook_generator import HookGenerator
from core.llm_client import LLMClient
from core.persona_generator import PersonaGenerator
from core.session_manager import SessionManager
from rag.context_retriever import ContextRetriever
from utils.cost_estimator import estimate


def render(llm: LLMClient, retriever: ContextRetriever, sm: SessionManager) -> None:
    st.subheader("Step 2 — Personas & Hooks")
    st.caption("Select which personas and hooks to include in your campaign.")

    brief = sm.get("client_brief", "")

    # Generate if not yet done
    if not sm.get("personas"):
        with st.spinner("Generating target personas..."):
            rag_ctx = retriever.retrieve_similar_campaigns(brief)
            sm.set("rag_context", rag_ctx)
            gen = PersonaGenerator(llm)
            personas = gen.generate(brief, rag_context=rag_ctx)
            sm.set("personas", personas)

    if not sm.get("hooks"):
        with st.spinner("Generating emotional hooks..."):
            hook_gen = HookGenerator(llm)
            hooks = hook_gen.generate(
                brief,
                personas=sm.get("personas", []),
                rag_context=sm.get("rag_context", ""),
            )
            sm.set("hooks", hooks)

    personas = sm.get("personas", [])
    hooks = sm.get("hooks", [])

    col_p, col_h = st.columns(2)

    # ── Personas ──────────────────────────────────────────────────────────────
    with col_p:
        st.markdown("### Target Personas")
        st.caption("Uncheck any you want to exclude")
        selected_p_ids = []
        for p in personas:
            checked = st.checkbox(
                f"**{p.name}**",
                value=True,
                key=f"persona_{p.id}",
                help=p.description,
            )
            if checked:
                selected_p_ids.append(p.id)
            with st.expander(p.name, expanded=False):
                st.write(p.description)
                if p.tags:
                    st.caption(" · ".join(p.tags))
        sm.set("selected_persona_ids", selected_p_ids)

    # ── Hooks ─────────────────────────────────────────────────────────────────
    with col_h:
        st.markdown("### Emotional Hooks")
        st.caption("Uncheck any you want to exclude")
        selected_h_ids = []
        for h in hooks:
            checked = st.checkbox(
                f"**{h.name}** `{h.hook_type}`",
                value=True,
                key=f"hook_{h.id}",
                help=h.description,
            )
            if checked:
                selected_h_ids.append(h.id)
            with st.expander(h.name, expanded=False):
                st.write(h.description)
        sm.set("selected_hook_ids", selected_h_ids)

    # ── Estimates ─────────────────────────────────────────────────────────────
    st.divider()
    n_p = len(selected_p_ids)
    n_h = len(selected_h_ids)

    if n_p > 0 and n_h > 0:
        engine = CombinationEngine()
        counts = engine.estimate_count(n_p, n_h)
        est = estimate(counts["total_rows"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Personas selected", n_p)
        m2.metric("Hooks selected", n_h)
        m3.metric("Total image prompts", counts["total_rows"])
        m4.metric("Estimated cost", f"${est['cost_usd']:.2f}")
        st.caption(f"Estimated generation time: {est['time_str']} · Provider: {est['provider']}")
    else:
        st.warning("Select at least 1 persona and 1 hook to continue.")

    st.divider()
    col_back, col_next = st.columns([1, 1])
    if col_back.button("← Back"):
        sm.go_to_step(1)
        st.rerun()
    if col_next.button(
        "Upload Product Image →",
        disabled=not (n_p > 0 and n_h > 0),
        type="primary",
    ):
        sm.advance_step()
        st.rerun()
