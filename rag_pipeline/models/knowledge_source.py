from django.db import models

from .constants import ResilienceFactor, SourceType
from .document import Document
from .mixins import TimestampMixin

CATEGORY_CHOICES = [
    ("interventions", "Interventions"),
    ("active_ingredients", "Active Ingredients"),
    ("evidence_base", "Evidence Base"),
    ("resources", "Resources"),
]


class KnowledgeSource(TimestampMixin):
    title = models.CharField(max_length=512)
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    resilience_factor = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        choices=ResilienceFactor.choices,
    )
    category = models.CharField(
        max_length=64,
        blank=True,
        choices=CATEGORY_CHOICES,
        help_text="Type of content in this source",
    )

    file = models.FileField(upload_to="raw_sources/", blank=True)
    url = models.URLField(blank=True)
    text = models.TextField(blank=True)

    document = models.OneToOneField(
        Document,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="knowledge_source",
    )

    class Meta:
        verbose_name = "Raw Knowledge Base Source"
        verbose_name_plural = "Raw Knowledge Base Sources"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, title='{self.title}', source_type='{self.source_type}')"

    def __str__(self):
        return f"[{self.get_source_type_display()}] {self.title}"

    @property
    def is_processed(self):
        return self.document_id is not None
