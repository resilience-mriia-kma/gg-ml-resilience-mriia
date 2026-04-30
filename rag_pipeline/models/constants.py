from django.db import models

from rag_pipeline.constants import DIMENSIONALITY, MAX_CHUNK_TOKENS  # noqa: F401


class SourceType(models.TextChoices):
    FILE = "file", "File upload"
    URL = "url", "Web page URL"
    TEXT = "text", "Pasted text"


class EmbeddingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    INDEXED = "indexed", "Indexed"
    STALE = "stale", "Stale"


class ResilienceFactor(models.TextChoices):
    FAMILY_SUPPORT = "family_support", "Family Support"
    OPTIMISM = "optimism", "Optimism"
    GOAL_DIRECTEDNESS = "goal_directedness", "Goal-Directedness / Coping"
    SOCIAL_CONNECTIONS = "social_connections", "Social Connections"
    HEALTH = "health", "Health"


class TargetResilienceLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class ImplementationDifficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"
