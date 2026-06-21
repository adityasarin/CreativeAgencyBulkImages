import os

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

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
    if st.button("🔄 Start Over", use_container_width=True):
        sm.reset()
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
render_current_step(sm, llm, retriever)
