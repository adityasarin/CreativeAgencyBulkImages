from image_gen.base_provider import BaseImageProvider


def create_provider() -> BaseImageProvider:
    from image_gen.gpt_image_provider import GptImageProvider
    return GptImageProvider()
