import json
import os
import re
from pathlib import Path

from core.llm_client import LLMClient
from core.models import ComboModel, PromptSetModel


class PromptBuilder:
    def __init__(self, llm: LLMClient):
        self._llm = llm
        self._template = self._load_template()

    def _load_template(self) -> str:
        path = os.getenv("SYSTEM_PROMPT_PATH", "SystemPrompt.txt")
        return Path(path).read_text(encoding="utf-8")

    def build_for_combo(
        self,
        combo: ComboModel,
        brand_context: str,
        product_visual: str = "Not provided",
        rag_prompt_context: str = "",
    ) -> PromptSetModel:
        system = self._inject(combo.persona_text, combo.hooks_text, brand_context, product_visual)

        user_msg = "Generate the image prompts now."
        if rag_prompt_context:
            user_msg = f"{rag_prompt_context}\n\n{user_msg}"

        raw = self._llm.chat_generation(
            [self._llm.user(user_msg)],
            system=system,
        )
        return self._parse(raw, combo.id)

    def _inject(
        self,
        persona_text: str,
        hooks_text: str,
        brand_context: str,
        product_visual: str,
    ) -> str:
        s = self._template
        s = s.replace("{PERSONA}", persona_text)
        s = s.replace("{HOOKS}", hooks_text)
        s = s.replace("{BRAND_CONTEXT}", brand_context)
        s = s.replace("{PRODUCT_VISUAL}", product_visual)
        return s

    def _parse(self, raw: str, combo_id: str) -> PromptSetModel:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        data = json.loads(text)
        meta = data.get("metadata", {})
        palette = meta.get("dominant_palette", "")
        if isinstance(palette, list):
            palette = ", ".join(palette)

        return PromptSetModel(
            combo_id=combo_id,
            creative_brief=data.get("creative_brief_summary", ""),
            prompt=data.get("image_generation_prompt", ""),
            negative_prompt=data.get("negative_prompt", ""),
            brand_name=meta.get("brand_name", ""),
            dominant_palette=palette,
            emotional_register=meta.get("emotional_register", ""),
            composition_type=meta.get("composition_type", ""),
            cta_zone=meta.get("recommended_cta_overlay_zone", ""),
            brand_alignment=meta.get("brand_alignment", ""),
            product_placement_zone=meta.get("product_placement_zone", ""),
            post_production_notes=meta.get("post_production_notes", ""),
        )
