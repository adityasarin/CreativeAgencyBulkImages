import json
import uuid

from core.llm_client import LLMClient
from core.models import HookModel, PersonaModel

_SYSTEM = """You are a world-class advertising copywriter and behavioural psychologist specialising in D2C performance marketing.
Your task: generate a diverse set of emotional advertising hooks for a product.
Each hook must be psychologically distinct and directly applicable to the product's real selling proposition.
Hooks should range from rational-emotional to deeply visceral. Never be generic."""

_USER_TEMPLATE = """{rag_context}

Product Brief:
{brief}

Selected Personas:
{persona_names}

Generate {n} distinct advertising hooks for this product. Each hook:
1. Has a short, punchy name (e.g. "Fear of Irreversible Decline", "Secret Weapon Envy", "Silent Shame")
2. A hook_type from: [fear, aspiration, fomo, authority, curiosity, belonging, comfort, playfulness, guilt, pride, urgency, nostalgia]
3. A description (2–3 sentences) explaining the psychological mechanism and how it drives purchase for this product
4. A brief trigger phrase (10 words max) that captures the emotional moment

Return ONLY a JSON array in this exact format:
[
  {{
    "name": "...",
    "hook_type": "...",
    "description": "...",
    "trigger_phrase": "..."
  }}
]"""


class HookGenerator:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def generate(
        self,
        brief: str,
        personas: list[PersonaModel],
        rag_context: str = "",
        n: int = 10,
    ) -> list[HookModel]:
        persona_names = ", ".join(p.name for p in personas) if personas else "general audience"
        prompt = _USER_TEMPLATE.format(
            brief=brief,
            rag_context=rag_context,
            persona_names=persona_names,
            n=n,
        )
        raw = self._llm.chat_generation([self._llm.user(prompt)], system=_SYSTEM)
        return self._parse(raw)

    def _parse(self, raw: str) -> list[HookModel]:
        try:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            return []
        hooks = []
        for item in data:
            desc = item.get("description", "")
            trigger = item.get("trigger_phrase", "")
            full_desc = f"{desc} Trigger: \"{trigger}\"" if trigger else desc
            hooks.append(HookModel(
                id=str(uuid.uuid4()),
                name=item.get("name", "Unknown"),
                hook_type=item.get("hook_type", "aspiration"),
                description=full_desc,
            ))
        return hooks
