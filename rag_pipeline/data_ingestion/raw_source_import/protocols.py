from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from rag_pipeline.data_ingestion.raw_source_import.dtos import RawChunk

if TYPE_CHECKING:
    from rag_pipeline.data_ingestion.raw_source_import.chunk_splitter import ChunkSplitter


class ISourceImporter(Protocol):
    """Contract for importing raw content from a specific source type."""

    def __init__(self, splitter: ChunkSplitter) -> None: ...

    def import_source(self, source: str, *, resilience_factor: str = "") -> list[RawChunk]: ...
