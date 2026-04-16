from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from rag_pipeline.retrieval.dtos import RetrievalResult


class IRetrievalService(Protocol):
    """Contract for the retrieval service (query -> ranked results)."""

    def retrieve(self, query: str, *, top_k: int = 5) -> list[RetrievalResult]: ...
