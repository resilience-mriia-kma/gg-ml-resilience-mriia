from django.db import models

# TODO: make this configurable and consistent with the embedding logic
MAX_CHUNK_TOKENS = 512
DIMENSIONALITY = 1536


class SourceType(models.TextChoices):
    FILE = "file", "File upload"
    URL = "url", "Web page URL"
    TEXT = "text", "Pasted text"


class EmbeddingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    INDEXED = "indexed", "Indexed"
    STALE = "stale", "Stale"
