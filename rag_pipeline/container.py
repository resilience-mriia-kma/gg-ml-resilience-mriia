from dependency_injector import containers, providers
from django.conf import settings

from rag_pipeline.constants import DIMENSIONALITY
from rag_pipeline.embedding.openai_embedding_service import OpenAIEmbeddingService
from rag_pipeline.llm.openai_llm_service import OpenAILLMService
from rag_pipeline.llm.prompt_builder import PromptBuilder
from rag_pipeline.retrieval.faiss_index import FAISSIndex


def build_rag_container() -> containers.DynamicContainer:
    """Build the RAG container.

    Imports that transitively touch Django models (VectorStore, Repository,
    RetrievalService, RAGService, RecommendationService) are deferred to
    this function because Django's app registry is not ready at module-load time.
    """
    from rag_pipeline.rag_service import RAGService
    from rag_pipeline.retrieval.repository import DocumentRepository
    from rag_pipeline.retrieval.retrieval_service import RetrievalService
    from rag_pipeline.retrieval.vector_store import VectorStore
    from resilience_app.recommendation_service import RecommendationService

    container = containers.DynamicContainer()

    container.embedder = providers.Singleton(OpenAIEmbeddingService)

    container.faiss_index = providers.Singleton(
        FAISSIndex,
        dimension=DIMENSIONALITY,
        index_path=settings.FAISS_INDEX_PATH,
    )

    container.repository = providers.Singleton(DocumentRepository)

    container.vector_store = providers.Singleton(
        VectorStore,
        index=container.faiss_index,
        embedder=container.embedder,
        repository=container.repository,
    )

    container.retrieval_service = providers.Singleton(
        RetrievalService,
        vector_store=container.vector_store,
    )

    container.llm_service = providers.Singleton(OpenAILLMService)
    container.prompt_builder = providers.Singleton(PromptBuilder)

    container.rag_service = providers.Singleton(
        RAGService,
        retrieval_service=container.retrieval_service,
        llm_service=container.llm_service,
        prompt_builder=container.prompt_builder,
    )

    container.recommendation_service = providers.Singleton(
        RecommendationService,
        rag_service=container.rag_service,
    )

    return container
