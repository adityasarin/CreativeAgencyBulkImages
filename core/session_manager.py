import threading
from typing import Any

import streamlit as st


_DEFAULTS: dict[str, Any] = {
    "current_step": 1,
    "stop_requested": False,
    "generation_running": False,
    "generation_complete": False,
    "client_name": "",
    "chat_history": [],
    "client_brief": "",
    "client_brief_model": None,
    "rag_context": "",
    "brand_context": "",
    "personas": [],
    "hooks": [],
    "selected_persona_ids": [],
    "selected_hook_ids": [],
    "product_image": None,
    "product_visual_context": "Not provided",
    "combo_matrix": [],
    "prompt_sets": [],
    "excel_rows": [],
    "excel_path": "",
    "filtered_rows": [],
    "generation_results": [],
    "output_dir": "",
    "run_dir": "",
    "report_path": "",
    "campaign_id": "",
    "feedback": {},
}


class SessionManager:
    @staticmethod
    def init() -> None:
        for key, default in _DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default
        if "gen_lock" not in st.session_state:
            st.session_state["gen_lock"] = threading.Lock()

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        st.session_state[key] = value

    @staticmethod
    def advance_step() -> None:
        st.session_state["current_step"] = min(
            st.session_state.get("current_step", 1) + 1, 6
        )

    @staticmethod
    def go_to_step(step: int) -> None:
        st.session_state["current_step"] = max(1, min(step, 6))

    @staticmethod
    def request_stop() -> None:
        st.session_state["stop_requested"] = True

    @staticmethod
    def is_stop_requested() -> bool:
        return st.session_state.get("stop_requested", False)

    @staticmethod
    def clear_stop() -> None:
        st.session_state["stop_requested"] = False

    @staticmethod
    def add_feedback(step: int, message: str) -> None:
        fb = st.session_state.setdefault("feedback", {})
        fb.setdefault(step, []).append(message)

    @staticmethod
    def get_feedback(step: int) -> list[str]:
        return st.session_state.get("feedback", {}).get(step, [])

    @staticmethod
    def reset() -> None:
        for key, default in _DEFAULTS.items():
            if isinstance(default, list):
                st.session_state[key] = []
            elif isinstance(default, dict):
                st.session_state[key] = {}
            else:
                st.session_state[key] = default
        st.session_state["gen_lock"] = threading.Lock()
