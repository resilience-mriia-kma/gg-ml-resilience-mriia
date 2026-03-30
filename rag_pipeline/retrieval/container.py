"""IoC container — wires up retrieval layer dependencies.

Provides lazy-initialized singletons for the FAISS index, repository, and vector store.
Management commands and application code resolve dependencies through this module.
"""

from __future__ import annotations

from functools import lru_cache

from django.conf import settings

from rag_pipeline.models import DIMENSIONALITY

from .faiss_index import FAISSIndex
from .protocol import IEmbedder, IVectorIndex
from .repository import DocumentRepository
from .vector_store import VectorStore


@lru_cache(maxsize=1)
def get_vector_index() -> IVectorIndex:
    index = FAISSIndex(dimension=DIMENSIONALITY, index_path=settings.FAISS_INDEX_PATH)
    index.load_or_create()
    return index


@lru_cache(maxsize=1)
def get_repository() -> DocumentRepository:
    return DocumentRepository()


def get_embedder() -> IEmbedder:
    # TODO: replace with real embedder once embedding module is implemented
    raise NotImplementedError("Embedder not yet configured — implement in rag_pipeline.embedding.embedder")


def get_vector_store() -> VectorStore:
    return VectorStore(
        index=get_vector_index(),
        embedder=get_embedder(),
        repository=get_repository(),
    )
