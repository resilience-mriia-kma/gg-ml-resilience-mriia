from django.db import models
from pgvector.django import HnswIndex, VectorField

# TODO: make this configurable and consistent with the embedding logic
MAX_CHUNK_TOKENS = 512 
DIMENSIONALITY = 1536 

    
class SourceType(models.TextChoices):
    FILE = 'file', 'File upload'
    URL = 'url', 'Web page URL'
    TEXT = 'text', 'Pasted text'

    
class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Document(TimestampMixin):
    title = models.CharField(max_length=512)
    source  = models.CharField(max_length=16, choices=SourceType.choices, null=True, blank=True)
    
    # an extra field to avoid querying all the chunks
    # TODO: consider using a Status field
    embedded_at = models.DateTimeField(null=True, blank=True) 

    class Meta:
        verbose_name = 'Processed Document'
        verbose_name_plural = 'Processed Documents'
        
    def __str__(self):
        return f"{self.__class__.__name__}: {self.title}"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, title='{self.title}', source='{self.source}')"

class DocumentChunk(TimestampMixin):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField(null=False, blank=False)
    token_count = models.PositiveIntegerField(default=0)
    embedding = VectorField(dimensions=1536, null=True, blank=True) # TODO: WIP - make dimensions configurable and consistent with the embedding logic

    class Meta:
        # TODO: configure vector index parameters (M, efConstruction) based on dataset size and expected query patterns
        indexes = [
            HnswIndex(
                name='document_embedding_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]
        verbose_name = 'Document Chunk'
        verbose_name_plural = 'Document Chunks'

    def __str__(self):
        return f"{self.__class__.__name__}: {self.title}"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, title='{self.title}', source='{self.source}')"


class KnowledgeSource(TimestampMixin):
    title = models.CharField(max_length=512)
    source_type = models.CharField(max_length=16, choices=SourceType.choices)

    file = models.FileField(upload_to='raw_sources/', blank=True)
    url = models.URLField(blank=True)
    text = models.TextField(blank=True)

    document = models.OneToOneField(
        Document, null=True, blank=True, on_delete=models.SET_NULL, related_name='source',
    )
    
    class Meta:
        verbose_name = 'Raw Knowledge Base Source'
        verbose_name_plural = 'Raw Knowledge Base Sources'
        
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, title='{self.title}', source_type='{self.source_type}')"

    def __str__(self):
        return f'[{self.get_source_type_display()}] {self.title}'

    @property
    def is_processed(self):
        return self.document_id is not None

