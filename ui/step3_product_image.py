import streamlit as st

from core.llm_client import LLMClient
from core.product_image_processor import ProductImageProcessor
from core.session_manager import SessionManager


def render(llm: LLMClient, sm: SessionManager) -> None:
    st.subheader("Step 3 — Product Image (Optional)")
    st.info(
        "Upload your product image as-is — we'll analyse it with AI to extract its colors "
        "and visual description, and ensure every generated ad is designed to showcase it. "
        "You can skip this step."
    )

    uploaded = st.file_uploader(
        "Upload product image (PNG or JPG)",
        type=["png", "jpg", "jpeg"],
        key="product_upload",
    )

    if uploaded:
        image_bytes = uploaded.read()
        with st.spinner("Analysing product image with AI..."):
            processor = ProductImageProcessor(llm)
            result = processor.process(image_bytes, uploaded.name)

        st.image(result.original_bytes, caption="Product image (used as-is)", use_column_width=True)

        # Color swatches
        st.markdown("**Extracted brand colors:**")
        swatch_html = "".join(
            f'<span style="display:inline-block;width:32px;height:32px;'
            f'border-radius:4px;background:{c};margin:4px;'
            f'border:1px solid #ccc;" title="{c}"></span>'
            for c in result.dominant_colors
        )
        st.markdown(swatch_html + " " + "  ".join(result.dominant_colors), unsafe_allow_html=True)

        # Editable visual description
        st.markdown("**AI visual description** *(injected into all image prompts — edit if needed)*")
        edited_desc = st.text_area(
            "Visual description",
            value=result.visual_description,
            height=120,
            key="product_desc_edit",
            label_visibility="collapsed",
        )

        if st.button("Use this image →", type="primary"):
            result.visual_description = edited_desc
            sm.set("product_image", result)
            sm.set("product_visual_context", edited_desc)
            sm.advance_step()
            st.rerun()

    st.divider()

    col_back, col_skip = st.columns([1, 1])
    if col_back.button("← Back"):
        sm.go_to_step(2)
        st.rerun()
    if col_skip.button("Skip — no product image"):
        sm.set("product_image", None)
        sm.set("product_visual_context", "Not provided")
        sm.advance_step()
        st.rerun()
