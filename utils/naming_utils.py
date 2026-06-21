import re
from core.models import ExcelRowModel


def slugify(text: str, max_len: int = 25) -> str:
    s = text.lower().strip()
    s = re.sub(r"[&/\\|+]", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-{2,}", "-", s)
    s = s.strip("-")
    return s[:max_len] if s else "unknown"


def make_image_filename(seq: int, row: ExcelRowModel) -> str:
    persona_slug = slugify(row.persona_name, 25)
    hook_slug = _hook_slug(row.hooks_text)
    return f"{seq:04d}_{persona_slug}_{hook_slug}.png"


def _hook_slug(hooks_text: str) -> str:
    parts = [h.strip() for h in hooks_text.replace("+", ",").split(",")]
    slugs = [slugify(p, 20) for p in parts if p]
    combined = "--".join(slugs)
    return combined[:40] if combined else "hook"
