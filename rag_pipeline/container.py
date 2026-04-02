from dependency_injector import containers, providers

from rag_pipeline.embedding.openai_embedding_service import OpenAIEmbeddingService
from rag_pipeline.llm.openai_llm_service import OpenAILLMService
from rag_pipeline.llm.prompt_builder import PromptBuilder
from rag_pipeline.rag_service import RAGService
from rag_pipeline.retrieval.retrieval_service import RetrievalService


class RAGContainer(containers.DeclarativeContainer):
    vector_store = providers.Dependency()

    embedding_service = providers.Singleton(OpenAIEmbeddingService)
    llm_service = providers.Singleton(OpenAILLMService)
    prompt_builder = providers.Singleton(PromptBuilder)

    retrieval_service = providers.Singleton(
        RetrievalService,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    rag_service = providers.Singleton(
        RAGService,
        retrieval_service=retrieval_service,
        llm_service=llm_service,
        prompt_builder=prompt_builder,
    )
