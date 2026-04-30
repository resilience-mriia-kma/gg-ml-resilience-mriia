from rag_pipeline.retrieval.dtos import RetrievalResult
from rag_pipeline.retrieval.protocols import IRetrievalService
from rag_pipeline.vectorstore.protocols import IVectorStore


class RetrievalService(IRetrievalService):
    def __init__(self, vector_store: IVectorStore) -> None:
        self.vector_store = vector_store

    def retrieve(self, query: str, *, profile: dict[str, str] | None = None, top_k: int = 5) -> list[RetrievalResult]:
        results = self.vector_store.search(query, k=top_k)
        return [
            RetrievalResult(
                chunk_id=r.chunk.pk,
                content=r.chunk.content,
                score=r.score,
                document_title=r.chunk.document.title,
            )
            for r in results
        ]
