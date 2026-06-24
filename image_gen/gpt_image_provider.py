import base64
import os

from image_gen.base_provider import BaseImageProvider


class GptImageProvider(BaseImageProvider):
    """OpenAI gpt-image-2 — returns base64-encoded PNGs directly (no URL fetch)."""

    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY", "")
        self._model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
        self._quality = os.getenv("OPENAI_IMAGE_QUALITY", "high")

    def generate(self, prompt: str, negative_prompt: str) -> bytes:
        import openai
        client = openai.OpenAI(api_key=self._api_key)
        response = client.images.generate(
            model=self._model,
            prompt=prompt,
            size="1024x1536",  # closest portrait size to 9:16
            quality=self._quality,
            n=1,
        )
        return base64.b64decode(response.data[0].b64_json)

    def get_provider_name(self) -> str:
        return self._model

    def get_cost_per_image_usd(self) -> float:
        return float(os.getenv("OPENAI_IMAGE_COST_USD", "0.10"))
