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
        # Split on Unicode circled numbers ①②③④
        sections = re.split(r"[①②③④]", raw)
        # sections[0] = preamble (ignore), [1]=brief, [2]=prompt, [3]=negative, [4]=metadata

        brief = sections[1].strip() if len(sections) > 1 else ""
        prompt = sections[2].strip().strip('"').strip() if len(sections) > 2 else raw.strip()
        neg_block = sections[3].strip() if len(sections) > 3 else ""
        meta_block = sections[4] if len(sections) > 4 else ""

        negative = re.sub(r"(?i)negative\s*prompt\s*[:\-]?\s*", "", neg_block).strip()

        return PromptSetModel(
            combo_id=combo_id,
            creative_brief=brief,
            prompt=prompt,
            negative_prompt=negative,
            brand_name=self._extract_meta(meta_block, "Brand Name"),
            dominant_palette=self._extract_meta(meta_block, "Dominant Palette"),
            emotional_register=self._extract_meta(meta_block, "Emotional Register"),
            composition_type=self._extract_meta(meta_block, "Composition Type"),
            cta_zone=self._extract_meta(meta_block, "Recommended CTA Overlay Zone"),
            brand_alignment=self._extract_meta(meta_block, "Brand Alignment"),
            product_placement_zone=self._extract_meta(meta_block, "Product Placement Zone"),
            post_production_notes=self._extract_meta(meta_block, "Post-Production Notes"),
        )

    @staticmethod
    def _extract_meta(block: str, key: str) -> str:
        pattern = rf"—\s*{re.escape(key)}\s*:\s*(.+?)(?=\n\s*—|\Z)"
        m = re.search(pattern, block, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return ""
