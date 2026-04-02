from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from rag_pipeline.models import Document, DocumentChunk, EmbeddingStatus


class IVectorIndex(Protocol):
    """Contract for any vector index backend (FAISS, etc.)."""

    def load_or_create(self) -> None: ...

    def save(self) -> None: ...

    def add(self, ids: NDArray[np.int64], vectors: NDArray[np.float32]) -> None: ...

    def remove(self, ids: NDArray[np.int64]) -> None: ...

    def search(self, query: NDArray[np.float32], k: int) -> tuple[NDArray[np.float32], NDArray[np.int64]]: ...

    def get_all_ids(self) -> NDArray[np.int64]: ...

    @property
    def count(self) -> int: ...


class IEmbedder(Protocol):
    """Contract for any embedding provider."""

    @property
    def dimension(self) -> int: ...

    def embed(self, text: str) -> NDArray[np.float32]: ...

    def embed_batch(self, texts: list[str]) -> NDArray[np.float32]: ...


class IDocumentRepository(Protocol):
    """Contract for document/chunk persistence operations."""

    def get_chunk_ids(self, document: Document) -> list[int]: ...

    def get_ordered_chunks(self, document: Document) -> list[DocumentChunk]: ...

    def get_chunks_by_ids(self, chunk_ids: list[int]) -> dict[int, DocumentChunk]: ...

    def update_document_status(self, document: Document, status: EmbeddingStatus) -> None: ...

    def get_all_chunk_ids(self) -> set[int]: ...

    def mark_documents_stale(self, chunk_ids: set[int]) -> int: ...
