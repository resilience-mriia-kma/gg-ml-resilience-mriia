from dependency_injector import containers, providers
from django.conf import settings

from rag_pipeline.constants import DIMENSIONALITY
from rag_pipeline.data_ingestion.raw_source_import.chunk_splitter import ChunkSplitter
from rag_pipeline.data_ingestion.raw_source_import.file_importer import FileImporter
from rag_pipeline.embedding.openai_embedding_service import OpenAIEmbeddingService
from rag_pipeline.llm.openai_llm_service import OpenAILLMService
from rag_pipeline.llm.prompt_builder import PromptBuilder
from rag_pipeline.rag_service import RAGService
from rag_pipeline.retrieval.retrieval_service import RetrievalService

# Factory functions use lazy imports so that container.py is importable without
# faiss/numpy being installed (those packages are only available on the server).
# The imports run the first time a provider is actually resolved.


def _make_faiss_index(dimension, index_path):
    from rag_pipeline.vectorstore.faiss_index import FAISSIndex

    index = FAISSIndex(dimension=dimension, index_path=index_path)
    index.load_or_create()
    return index


def _make_repository():
    from rag_pipeline.vectorstore.repository import DocumentRepository

    return DocumentRepository()


def _make_vector_store(index, embedder, repository):
    from rag_pipeline.vectorstore.vector_store import VectorStore

    return VectorStore(index=index, embedder=embedder, repository=repository)


def _make_ingestion_pipeline(file_importer, repository, vector_store):
    from rag_pipeline.data_ingestion.pipeline import IngestionPipeline

    return IngestionPipeline(file_importer=file_importer, repository=repository, vector_store=vector_store)


class RAGContainer(containers.DeclarativeContainer):
    embedding_service = providers.Singleton(OpenAIEmbeddingService)
    llm_service = providers.Singleton(OpenAILLMService)
    prompt_builder = providers.Singleton(PromptBuilder)

    faiss_index = providers.Singleton(
        _make_faiss_index,
        dimension=DIMENSIONALITY,
        index_path=providers.Callable(lambda: settings.FAISS_INDEX_PATH),
    )

    repository = providers.Singleton(_make_repository)

    vector_store = providers.Singleton(
        _make_vector_store,
        index=faiss_index,
        embedder=embedding_service,
        repository=repository,
    )

    chunk_splitter = providers.Singleton(ChunkSplitter)
    file_importer = providers.Singleton(FileImporter, splitter=chunk_splitter)

    ingestion_pipeline = providers.Singleton(
        _make_ingestion_pipeline,
        file_importer=file_importer,
        repository=repository,
        vector_store=vector_store,
    )

    retrieval_service = providers.Singleton(
        RetrievalService,
        vector_store=vector_store,
    )

    rag_service = providers.Singleton(
        RAGService,
        retrieval_service=retrieval_service,
        llm_service=llm_service,
        prompt_builder=prompt_builder,
    )
