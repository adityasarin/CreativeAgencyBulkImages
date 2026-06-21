import streamlit as st

from core.llm_client import LLMClient
from core.session_manager import SessionManager
from rag.chroma_store import ChromaStore
from rag.context_retriever import ContextRetriever


def render_current_step(sm: SessionManager, llm: LLMClient, retriever: ContextRetriever) -> None:
    step = sm.get("current_step", 1)

    if step == 1:
        from ui.step1_chat import render
        render(llm, sm)

    elif step == 2:
        from ui.step2_personas import render
        render(llm, retriever, sm)

    elif step == 3:
        from ui.step3_product_image import render
        render(llm, sm)

    elif step == 4:
        from ui.step4_matrix import render
        render(llm, retriever, sm)

    elif step == 5:
        from ui.step5_excel import render
        render(sm)

    elif step == 6:
        from ui.step6_generation import render
        render(sm)
