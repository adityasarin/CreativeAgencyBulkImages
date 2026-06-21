import json

from core.llm_client import LLMClient
from core.models import ClientBriefModel

_EXTRACT_SYSTEM = """You are a brand strategist. Extract structured brand information from a client brief.
Return ONLY valid JSON, no other text."""

_EXTRACT_USER = """From this client brief, extract the following as JSON:
{{
  "product_name": "...",
  "product_description": "...",
  "brand_palette": "...",
  "brand_tone": "...",
  "campaign_goal": "..."
}}

If a field is not mentioned, make a reasonable inference from context.

Client Brief:
{brief}"""


class BrandContextBuilder:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def extract_brief_model(self, raw_brief: str) -> ClientBriefModel:
        prompt = _EXTRACT_USER.format(brief=raw_brief)
        raw = self._llm.chat_simple([self._llm.user(prompt)], system=_EXTRACT_SYSTEM)
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            data = {}
        return ClientBriefModel(
            product_name=data.get("product_name", "Product"),
            product_description=data.get("product_description", raw_brief[:200]),
            brand_palette=data.get("brand_palette", "not specified"),
            brand_tone=data.get("brand_tone", "professional"),
            campaign_goal=data.get("campaign_goal", "awareness and consideration"),
        )

    def build(self, brief_model: ClientBriefModel, rag_context: str = "") -> str:
        lines = [
            f"Brand: {brief_model.product_name}",
            f"Product: {brief_model.product_description}",
            f"Brand Palette: {brief_model.brand_palette}",
            f"Brand Tone: {brief_model.brand_tone}",
            f"Campaign Goal: {brief_model.campaign_goal}",
        ]
        if rag_context:
            lines.append(rag_context)
        return "\n".join(lines)
