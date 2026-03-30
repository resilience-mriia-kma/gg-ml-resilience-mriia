from django.db import models

from .constants import EmbeddingStatus, SourceType
from .mixins import TimestampMixin


class Document(TimestampMixin):
    title = models.CharField(max_length=512)
    source = models.CharField(max_length=16, choices=SourceType.choices, default="", blank=True)
    embedding_status = models.CharField(
        max_length=16,
        choices=EmbeddingStatus.choices,
        default=EmbeddingStatus.PENDING,
    )
    indexed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Processed Document"
        verbose_name_plural = "Processed Documents"

    def __str__(self):
        return f"{self.__class__.__name__}: {self.title}"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, title='{self.title}', source='{self.source}')"


class DocumentChunk(TimestampMixin):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField(null=False, blank=False)
    token_count = models.PositiveIntegerField(default=0)
    chunk_index = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["chunk_index"]
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        return f"{self.__class__.__name__}: doc={self.document_id}, idx={self.chunk_index}"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})"
        )
