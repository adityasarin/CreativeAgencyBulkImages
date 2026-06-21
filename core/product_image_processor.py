import io

from PIL import Image

from core.llm_client import LLMClient
from core.models import ProcessedProductImage

_VISION_SYSTEM = "You are a product photographer writing descriptions for AI image generation systems."

_VISION_USER = """Describe this product for direct injection into an AI image generation prompt (Stable Diffusion / DALL-E).

Include ALL of the following in a single dense comma-separated descriptor string:
1. Product form and silhouette (shape, overall proportions)
2. Surface finish and texture (matte/glossy/brushed/soft-touch etc.)
3. Distinctive visual features (edges, cutouts, patterns, embossing, hardware)
4. Scale and proportions relative to everyday objects
5. Dominant colors — use these extracted hex values: {colors}

Rules:
- Max 120 words
- Comma-separated phrases only, no sentences
- No brand names, no marketing language
- Write as if describing the object for a blind sculptor who must reproduce it exactly"""


class ProductImageProcessor:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def process(self, image_bytes: bytes, filename: str) -> ProcessedProductImage:
        original = image_bytes

        # 1. Normalize to RGBA PNG, used as-is (no AI background removal)
        cleaned = self._to_rgba_png(image_bytes)

        # 2. Resize (max 800px on longest side, preserve aspect)
        cleaned = self._resize_normalized(cleaned)

        # 3. Extract dominant colors
        colors = self._extract_colors(cleaned)

        # 4. Analyze with vision
        description = self._analyze_with_vision(cleaned, colors)

        img = Image.open(io.BytesIO(cleaned))
        w, h = img.size

        return ProcessedProductImage(
            original_bytes=original,
            cleaned_png_bytes=cleaned,
            dominant_colors=colors,
            visual_description=description,
            width=w,
            height=h,
            filename=filename,
        )

    def _to_rgba_png(self, image_bytes: bytes) -> bytes:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _resize_normalized(self, image_bytes: bytes, max_side: int = 800) -> bytes:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((max_side, max_side), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _extract_colors(self, image_bytes: bytes, n: int = 3) -> list[str]:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        rgb_pixels = [
            (r, g, b)
            for r, g, b, a in img.getdata()
            if a > 10  # exclude transparent pixels
        ]
        if not rgb_pixels:
            return ["#888888"]

        # Quantize to n colors via PIL
        small = Image.new("RGB", (1, len(rgb_pixels)))
        small.putdata(rgb_pixels)
        quantized = small.quantize(colors=n, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()

        colors = []
        for i in range(n):
            r, g, b = palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]
            colors.append(f"#{r:02X}{g:02X}{b:02X}")
        return colors

    def _analyze_with_vision(self, image_bytes: bytes, colors: list[str]) -> str:
        user_prompt = _VISION_USER.format(colors=", ".join(colors))
        try:
            return self._llm.chat_vision(image_bytes, user_prompt, system=_VISION_SYSTEM)
        except Exception:
            return f"product with dominant colors {', '.join(colors)}, clean form, professional finish"
