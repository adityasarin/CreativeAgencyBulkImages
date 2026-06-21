import streamlit as st

from core.excel_manager import ExcelManager
from core.session_manager import SessionManager
from utils.cost_estimator import estimate


def render(sm: SessionManager) -> None:
    st.subheader("Step 5 — Review & Select Prompts")

    manager = ExcelManager()
    client_name = sm.get("client_name", "client")
    excel_rows = sm.get("excel_rows", [])

    # ── Section A: Download ───────────────────────────────────────────────────
    st.markdown("### Download Prompt Spreadsheet")
    st.info(
        "Open the Excel file, review all prompts, and set **select_flag** to **FALSE** "
        "for any prompts you want to skip. Then re-upload below."
    )

    filename, excel_bytes = manager.write_excel(excel_rows, client_name)
    sm.set("excel_path", filename)

    st.download_button(
        label="⬇ Download Excel",
        data=excel_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Preview table
    if excel_rows:
        import pandas as pd
        preview = pd.DataFrame([{
            "Persona": r.persona_name,
            "Hooks": r.hooks_text,
            "Prompt (preview)": r.prompt[:80] + "...",
            "Select": r.select_flag,
        } for r in excel_rows[:20]])
        st.dataframe(preview, use_container_width=True)
        if len(excel_rows) > 20:
            st.caption(f"Showing 20 of {len(excel_rows)} rows. Download the full file to see all.")

    st.divider()

    # ── Section B: Upload ─────────────────────────────────────────────────────
    st.markdown("### Upload Edited Spreadsheet")
    uploaded = st.file_uploader(
        "Upload your edited Excel file",
        type=["xlsx"],
        key="excel_upload",
    )

    if uploaded:
        valid, error = manager.validate_schema(uploaded)
        if not valid:
            st.error(f"Invalid file: {error}")
        else:
            uploaded.seek(0)
            all_rows = manager.read_excel(uploaded)
            selected = [r for r in all_rows if r.select_flag]
            skipped = len(all_rows) - len(selected)

            sm.set("filtered_rows", selected)

            st.success(f"**{len(selected)}** prompts selected · **{skipped}** skipped")

            # Metrics
            est = estimate(len(selected))
            m1, m2, m3 = st.columns(3)
            m1.metric("Images to Generate", len(selected))
            m2.metric("Estimated Cost", f"${est['cost_usd']:.2f}")
            m3.metric("Estimated Time", est["time_str"])

            # Preview selected
            import pandas as pd
            sel_df = pd.DataFrame([{
                "Persona": r.persona_name,
                "Hooks": r.hooks_text,
            } for r in selected])
            st.dataframe(sel_df, use_container_width=True)

    st.divider()
    col_back, col_next = st.columns([1, 1])
    if col_back.button("← Back"):
        sm.go_to_step(4)
        st.rerun()

    filtered = sm.get("filtered_rows", [])
    if col_next.button(
        "Start Image Generation →",
        disabled=not filtered,
        type="primary",
    ):
        sm.advance_step()
        st.rerun()
