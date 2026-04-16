from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from rag_pipeline.models import Document, DocumentChunk, EmbeddingStatus
    from rag_pipeline.retrieval.dtos import RetrievalResult, SearchResult


class IVectorIndex(Protocol):
    """Contract for any vector index backend"""

    def load_or_create(self) -> None: ...

    def save(self) -> None: ...

    def add(self, ids: NDArray[np.int64], vectors: NDArray[np.float32]) -> None: ...

    def remove(self, ids: NDArray[np.int64]) -> None: ...

    def search(self, query: NDArray[np.float32], k: int) -> tuple[NDArray[np.float32], NDArray[np.int64]]: ...

    def get_all_ids(self) -> NDArray[np.int64]: ...

    @property
    def count(self) -> int: ...


class IDocumentRepository(Protocol):
    """Contract for document/chunk persistence operations."""

    def get_chunk_ids(self, document: Document) -> list[int]: ...

    def get_ordered_chunks(self, document: Document) -> list[DocumentChunk]: ...

    def get_chunks_by_ids(self, chunk_ids: list[int]) -> dict[int, DocumentChunk]: ...

    def update_document_status(self, document: Document, status: EmbeddingStatus) -> None: ...

    def get_all_chunk_ids(self) -> set[int]: ...

    def mark_documents_stale(self, chunk_ids: set[int]) -> int: ...


class IVectorStore(Protocol):
    """Contract for the vector store coordinator (index + DB + embedding)."""

    def index_document(self, document: Document) -> int: ...

    def remove_document(self, document: Document) -> int: ...

    def search(self, query: str, k: int = 10) -> list[SearchResult]: ...

    def reindex_document(self, document: Document) -> int: ...


class IRetrievalService(Protocol):
    """Contract for the retrieval service (query -> ranked results)."""

    def retrieve(self, query: str, *, top_k: int = 5) -> list[RetrievalResult]: ...
