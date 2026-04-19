from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from rag_pipeline.rag_service import RAGResponse


class IRAGService(Protocol):
    def answer(self, query: str, *, top_k: int = 5) -> RAGResponse: ...
