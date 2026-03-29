from django.db import models
from pgvector.django import HnswIndex, VectorField

class Document(models.Model):
    title = models.CharField(max_length=512)
    source = models.URLField(blank=True)
    content = models.TextField()
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            HnswIndex(
                name='document_embedding_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]

    def __str__(self):
        return self.title


class AnalysisRequest(models.Model):
    class ResilienceLevel(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    teacher_id = models.CharField(max_length=128)
    student_id = models.CharField(max_length=128)
    student_age = models.PositiveSmallIntegerField()
    student_gender = models.CharField(max_length=64)

    # Raw scores per factor stored as JSON lists
    scores = models.JSONField(
        help_text='Dict of factor_key -> list of scores (0/1/2/NA)',
    )

    # Computed profile per factor
    profile = models.JSONField(
        blank=True,
        default=dict,
        help_text='Dict of factor_key -> low/medium/high',
    )

    recommendations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Request {self.pk} — teacher {self.teacher_id}, student {self.student_id}'
