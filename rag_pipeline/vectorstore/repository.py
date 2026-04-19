from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from rag_pipeline.data_ingestion.raw_source_import.dtos import RawChunk
from rag_pipeline.models import Document, DocumentChunk, EmbeddingStatus, SourceType

from .protocols import IDocumentRepository


class DocumentRepository(IDocumentRepository):
    """Django ORM implementation of IDocumentRepository."""

    def get_chunk_ids(self, document: Document) -> list[int]:
        return list(document.chunks.values_list("pk", flat=True))

    def get_ordered_chunks(self, document: Document) -> list[DocumentChunk]:
        return list(document.chunks.order_by("chunk_index"))

    def get_chunks_by_ids(self, chunk_ids: list[int]) -> dict[int, DocumentChunk]:
        chunks = DocumentChunk.objects.filter(pk__in=chunk_ids).select_related("document")
        return {c.pk: c for c in chunks}

    def update_document_status(self, document: Document, status: EmbeddingStatus) -> None:
        document.embedding_status = status
        document.indexed_at = timezone.now() if status == EmbeddingStatus.INDEXED else None
        document.save(update_fields=["embedding_status", "indexed_at"])

    def get_all_chunk_ids(self) -> set[int]:
        return set(DocumentChunk.objects.values_list("pk", flat=True))

    def mark_documents_stale(self, chunk_ids: set[int]) -> int:
        return (
            Document.objects.filter(chunks__pk__in=chunk_ids).distinct().update(embedding_status=EmbeddingStatus.STALE)
        )

    def create_document_with_chunks(self, title: str, source: SourceType, chunks: list[RawChunk]) -> Document:
        with transaction.atomic():
            document = Document.objects.create(
                title=title,
                source=source,
                embedding_status=EmbeddingStatus.PENDING,
            )
            DocumentChunk.objects.bulk_create([
                DocumentChunk(
                    document=document,
                    content=chunk.content,
                    resilience_factor=chunk.resilience_factor,
                    token_count=chunk.token_count,
                    chunk_index=chunk.chunk_index,
                )
                for chunk in chunks
            ])
        return document
