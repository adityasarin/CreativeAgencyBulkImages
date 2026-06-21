from abc import ABC, abstractmethod


class BaseImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, negative_prompt: str) -> bytes:
        """Generate an image and return raw PNG bytes."""

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    @abstractmethod
    def get_cost_per_image_usd(self) -> float:
        pass
