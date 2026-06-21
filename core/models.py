from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PersonaModel:
    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)


@dataclass
class HookModel:
    id: str
    name: str
    hook_type: str  # fear | aspiration | fomo | authority | curiosity | belonging | comfort | playfulness
    description: str


@dataclass
class ComboModel:
    id: str
    persona: PersonaModel
    hooks: list[HookModel]  # 1 or 2
    persona_text: str       # formatted for {PERSONA}
    hooks_text: str         # formatted for {HOOKS}


@dataclass
class ProcessedProductImage:
    original_bytes: bytes
    cleaned_png_bytes: bytes   # RGBA PNG, background removed
    dominant_colors: list[str] # hex codes e.g. ["#9EA3A8", "#3D2B1F"]
    visual_description: str    # GPT vision output — injected as {PRODUCT_VISUAL}
    width: int
    height: int
    filename: str


@dataclass
class ClientBriefModel:
    product_name: str
    product_description: str
    brand_palette: str   # e.g. "charcoal black, honey-oak, brushed steel"
    brand_tone: str      # e.g. "quiet mastery, understated craftsmanship"
    campaign_goal: str


@dataclass
class PromptSetModel:
    combo_id: str
    creative_brief: str
    prompt: str
    negative_prompt: str
    brand_name: str
    dominant_palette: str
    emotional_register: str
    composition_type: str
    cta_zone: str
    brand_alignment: str
    product_placement_zone: str
    post_production_notes: str


@dataclass
class ExcelRowModel:
    row_id: str
    client_name: str
    persona_id: str
    persona_name: str
    persona_description: str
    hook_ids: str        # comma-separated UUIDs
    hooks_text: str
    prompt: str
    negative_prompt: str
    creative_brief: str
    brand_name: str
    dominant_palette: str
    emotional_register: str
    composition_type: str
    cta_zone: str
    brand_alignment: str
    product_placement_zone: str
    select_flag: bool    # True = generate, False = skip


@dataclass
class GenerationResultModel:
    row_id: str
    client_name: str
    persona_name: str
    hooks_text: str
    prompt: str
    negative_prompt: str
    image_path: str
    image_filename: str
    provider: str        # dalle3
    status: str          # success | failed | skipped
    error_message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_time_sec: float = 0.0
    cost_usd: float = 0.04
