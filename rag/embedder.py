# Thin wrapper — ChromaStore uses the embedding function directly.
# This module exists for standalone testing of the embedding model.

from chromadb.utils import embedding_functions


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._ef(texts)

    def embed_single(self, text: str) -> list[float]:
        return self._ef([text])[0]
