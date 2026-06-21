import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


def _ef():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )


class ChromaStore:
    def __init__(self):
        path = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
        Path(path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=path)
        self._ef = _ef()

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        return self._client.get_or_create_collection(
            name=name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        col = self.get_or_create_collection(collection_name)
        col.upsert(documents=documents, metadatas=metadatas, ids=ids)

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 3,
    ) -> list[dict]:
        col = self.get_or_create_collection(collection_name)
        if col.count() == 0:
            return []
        n_results = min(n_results, col.count())
        result = col.query(query_texts=[query_text], n_results=n_results)
        out = []
        for doc, meta, dist in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        ):
            out.append({"document": doc, "metadata": meta, "distance": dist})
        return out

    def collection_count(self, name: str) -> int:
        try:
            return self.get_or_create_collection(name).count()
        except Exception:
            return 0
