import streamlit as st

from core.llm_client import LLMClient
from core.session_manager import SessionManager

_SYSTEM = """You are a creative agency account manager onboarding a new client campaign.
Your job: through friendly conversation, gather all the information needed to generate advertising personas and hooks.

Ask about: product name, what it does, unique selling points, target audience, price point, campaign objective,
any emotional territory the client wants to own, competitor context, and brand personality.

Keep it conversational. Ask 1–2 questions at a time.
When you have enough (product + audience + goal), end your message with exactly this token: [BRIEF_READY]
Then write a final consolidated brief paragraph summarising everything."""


def render(llm: LLMClient, sm: SessionManager) -> None:
    st.subheader("Step 1 — Tell us about your client")
    st.caption("Chat with our AI account manager to build the campaign brief.")

    # Client name
    client_name = st.text_input(
        "Client / Project Name",
        value=sm.get("client_name", ""),
        placeholder="e.g. GrillForge Q3 Campaign",
        key="client_name_input",
    )
    if client_name:
        sm.set("client_name", client_name)

    st.divider()

    # Chat display
    history = sm.get("chat_history", [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Initial prompt if empty
    if not history:
        with st.chat_message("assistant"):
            opening = "Hi! I'm your AI account manager. Let's build your campaign brief.\n\nTo start — **what's the product name**, and in one sentence, what does it do?"
            st.markdown(opening)
        sm.set("chat_history", [{"role": "assistant", "content": opening}])
        st.rerun()

    # User input
    if user_input := st.chat_input("Type your message..."):
        history = sm.get("chat_history", [])
        history.append({"role": "user", "content": user_input})
        sm.set("chat_history", history)

        with st.chat_message("user"):
            st.markdown(user_input)

        # Stream assistant response
        messages = [{"role": m["role"], "content": m["content"]} for m in history]
        with st.chat_message("assistant"):
            response_box = st.empty()
            full = ""
            for chunk in llm.stream_simple(messages, system=_SYSTEM):
                full += chunk
                response_box.markdown(full + "▌")
            response_box.markdown(full)

        history.append({"role": "assistant", "content": full})
        sm.set("chat_history", history)

        # Check if brief is ready
        if "[BRIEF_READY]" in full:
            before, _, after = full.partition("[BRIEF_READY]")
            brief = after.strip() or before.strip()
            sm.set("client_brief", brief)
            st.success("Brief captured! You can now generate personas and hooks.")

        st.rerun()

    # Navigation
    st.divider()
    brief_ready = bool(sm.get("client_brief"))

    if history and not brief_ready:
        if st.button("Brief is done — summarise it for me"):
            messages = [{"role": m["role"], "content": m["content"]} for m in history]
            summary_prompt = (
                "Based on our conversation so far, write a final consolidated brief "
                "paragraph summarising the product, target audience, price point, "
                "campaign objective, emotional territory, competitor context, and "
                "brand personality. Output only the brief paragraph, nothing else."
            )
            messages.append({"role": "user", "content": summary_prompt})
            brief = llm.chat_simple(messages, system=_SYSTEM)
            sm.set("client_brief", brief)
            st.rerun()

    col1, col2 = st.columns([2, 1])
    col1.info("Continue chatting until the brief is complete, then click Next.")
    if col2.button(
        "Generate Personas & Hooks →",
        disabled=not (client_name and brief_ready),
        type="primary",
    ):
        sm.advance_step()
        st.rerun()
