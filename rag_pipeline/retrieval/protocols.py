from typing import Protocol

from rag_pipeline.retrieval.dtos import RetrievalResult


class IVectorStore(Protocol):
    def search(self, query_embedding: list[float], *, top_k: int = 5) -> list[RetrievalResult]: ...
