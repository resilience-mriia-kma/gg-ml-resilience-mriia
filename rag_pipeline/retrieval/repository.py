from __future__ import annotations

from django.utils import timezone

from rag_pipeline.models import Document, DocumentChunk, EmbeddingStatus

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
