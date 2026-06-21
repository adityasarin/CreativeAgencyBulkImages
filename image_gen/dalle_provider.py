import io
import os

import requests

from image_gen.base_provider import BaseImageProvider


class DalleProvider(BaseImageProvider):
    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY", "")

    def generate(self, prompt: str, negative_prompt: str) -> bytes:
        import openai
        client = openai.OpenAI(api_key=self._api_key)
        # DALL-E 3 closest portrait size to 9:16
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",
            quality="standard",
            n=1,
        )
        url = response.data[0].url
        img_resp = requests.get(url, timeout=60)
        img_resp.raise_for_status()
        return img_resp.content

    def get_provider_name(self) -> str:
        return "dalle3"

    def get_cost_per_image_usd(self) -> float:
        return 0.08
