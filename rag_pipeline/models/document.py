from django.db import models
from pgvector.django import HnswIndex, VectorField

from .constants import DIMENSIONALITY, SourceType
from .mixins import TimestampMixin


class Document(TimestampMixin):
    title = models.CharField(max_length=512)
    source = models.CharField(max_length=16, choices=SourceType.choices, null=True, blank=True)

    # an extra field to avoid querying all the chunks
    # TODO: consider using a Status field
    embedded_at = models.DateTimeField(null=True, blank=True)

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
    embedding = VectorField(dimensions=DIMENSIONALITY, null=True, blank=True)

    class Meta:
        # TODO: configure vector index parameters (M, efConstruction) based on dataset size and expected query patterns
        indexes = [
            HnswIndex(
                name="document_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        return f"{self.__class__.__name__}: {self.title}"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, title='{self.title}', source='{self.source}')"
