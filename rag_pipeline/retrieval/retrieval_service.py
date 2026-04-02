from rag_pipeline.retrieval.dtos import RetrievalResult
from rag_pipeline.retrieval.vector_store import VectorStore


class RetrievalService:
    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    def retrieve(self, query: str, *, top_k: int = 5) -> list[RetrievalResult]:
        search_results = self.vector_store.search(query, k=top_k)
        return [
            RetrievalResult(
                chunk_id=r.chunk.pk,
                content=r.chunk.content,
                score=r.score,
                document_title=r.chunk.document.title,
            )
            for r in search_results
        ]
