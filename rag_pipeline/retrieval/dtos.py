from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag_pipeline.models import DocumentChunk


@dataclass(frozen=True)
class SearchResult:
    chunk: DocumentChunk
    score: float


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: int
    content: str
    score: float
    document_title: str
