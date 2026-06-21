from image_gen.base_provider import BaseImageProvider


def create_provider() -> BaseImageProvider:
    from image_gen.dalle_provider import DalleProvider
    return DalleProvider()
