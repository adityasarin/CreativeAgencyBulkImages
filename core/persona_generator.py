import json
import uuid

from core.llm_client import LLMClient
from core.models import PersonaModel

_SYSTEM = """You are a senior consumer insights strategist with deep expertise in audience segmentation for D2C brands.
Your task: given a product brief, generate a diverse set of highly specific target personas.
Each persona must be directly relevant to the product and represent a real, reachable audience segment.
Be creative and thorough — surface non-obvious segments that marketing teams often miss."""

_USER_TEMPLATE = """{rag_context}

Product Brief:
{brief}

Generate {n} distinct target personas for this product. For each persona:
1. Give a short, memorable name (e.g. "Type 2 Diabetics", "Health-Anxious Millennials", "Competitive Amateur Athletes")
2. A detailed description (3–4 sentences) covering: demographics, psychographics, pain points, motivations, and how this product fits their life
3. A list of 3–5 single-word tags (e.g. ["health", "age_30_45", "urban"])
4. A hook_type most likely to resonate: one of [fear, aspiration, fomo, authority, curiosity, belonging, comfort, playfulness]

Return ONLY a JSON array in this exact format:
[
  {{
    "name": "...",
    "description": "...",
    "tags": ["...", "..."],
    "hook_type": "..."
  }}
]"""


class PersonaGenerator:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def generate(self, brief: str, rag_context: str = "", n: int = 8) -> list[PersonaModel]:
        prompt = _USER_TEMPLATE.format(brief=brief, rag_context=rag_context, n=n)
        raw = self._llm.chat_generation([self._llm.user(prompt)], system=_SYSTEM)
        return self._parse(raw)

    def _parse(self, raw: str) -> list[PersonaModel]:
        try:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            return []
        personas = []
        for item in data:
            personas.append(PersonaModel(
                id=str(uuid.uuid4()),
                name=item.get("name", "Unknown"),
                description=item.get("description", ""),
                tags=item.get("tags", []),
            ))
        return personas
