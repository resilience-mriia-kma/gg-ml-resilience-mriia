from rag_pipeline.embedding.protocols import IEmbeddingService
from rag_pipeline.retrieval.dtos import RetrievalResult
from rag_pipeline.retrieval.protocols import IVectorStore


class RetrievalService:
    def __init__(self, embedding_service: IEmbeddingService, vector_store: IVectorStore) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(self, query: str, *, top_k: int = 5) -> list[RetrievalResult]:
        query_embedding = self.embedding_service.embed(query)
        return self.vector_store.search(query_embedding, top_k=top_k)
