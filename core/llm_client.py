import base64
import os
from typing import Generator

import openai


class LLMClient:
    def __init__(self):
        self._client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._mini = os.getenv("OPENAI_MINI_MODEL", "gpt-4o-mini")
        self._main = os.getenv("OPENAI_MAIN_MODEL", "gpt-4o")

    # ── Simple / extraction tasks (mini model) ───────────────────────────────

    def chat_simple(self, messages: list[dict], system: str = "") -> str:
        resp = self._client.chat.completions.create(
            model=self._mini,
            max_tokens=2048,
            messages=self._with_system(system, messages),
        )
        return resp.choices[0].message.content

    def stream_simple(self, messages: list[dict], system: str = "") -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self._mini,
            max_tokens=2048,
            messages=self._with_system(system, messages),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    # ── Creative generation tasks (main model) ───────────────────────────────

    def chat_generation(self, messages: list[dict], system: str = "") -> str:
        resp = self._client.chat.completions.create(
            model=self._main,
            max_tokens=4096,
            messages=self._with_system(system, messages),
        )
        return resp.choices[0].message.content

    # ── Vision tasks (main model with image content block) ───────────────────

    def chat_vision(self, image_bytes: bytes, user_prompt: str, system: str = "") -> str:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ]
        resp = self._client.chat.completions.create(
            model=self._main,
            max_tokens=512,
            messages=self._with_system(system, messages),
        )
        return resp.choices[0].message.content

    # ── Helper ───────────────────────────────────────────────────────────────

    @staticmethod
    def _with_system(system: str, messages: list[dict]) -> list[dict]:
        return [{"role": "system", "content": system}, *messages] if system else messages

    @staticmethod
    def user(content: str) -> dict:
        return {"role": "user", "content": content}

    @staticmethod
    def assistant(content: str) -> dict:
        return {"role": "assistant", "content": content}
