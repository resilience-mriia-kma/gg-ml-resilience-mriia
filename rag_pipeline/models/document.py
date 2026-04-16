from django.db import models

from .constants import EmbeddingStatus, SourceType
from .mixins import TimestampMixin


class Document(TimestampMixin):
    chunks: models.QuerySet["DocumentChunk"]

    title = models.CharField(max_length=512)
    source = models.CharField(max_length=16, choices=SourceType.choices, default="", blank=True)
    embedding_status = models.CharField(
        max_length=16,
        choices=EmbeddingStatus.choices,
        default=EmbeddingStatus.PENDING,
    )
    indexed_at = models.DateTimeField(null=True, blank=True)

    class Meta(TimestampMixin.Meta):
        verbose_name = "Processed Document"
        verbose_name_plural = "Processed Documents"

    def __str__(self):
        return f"{self.__class__.__name__}: {self.title}"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.pk}, title='{self.title}', source='{self.source}')"


class DocumentChunk(TimestampMixin):
    document_id: int

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField(null=False, blank=False)
    resilience_factor = models.CharField(max_length=64, blank=True, db_index=True)
    # values: "family_support", "optimism", "goal_directedness", "social_connections", "health", or "" if unknown
    token_count = models.PositiveIntegerField(default=0)
    chunk_index = models.PositiveIntegerField(default=0)

    class Meta(TimestampMixin.Meta):
        ordering = ["chunk_index"]
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        return f"{self.__class__.__name__}: doc={self.document_id}, idx={self.chunk_index}"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(id={self.pk}, document_id={self.document_id}, chunk_index={self.chunk_index})"
        )
