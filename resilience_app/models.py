from django.db import models


class TeacherProfile(models.Model):
    class FeedbackStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        DECLINED = "declined", "Declined"
        SUBMITTED = "submitted", "Submitted"

    teacher_id = models.CharField(max_length=128, unique=True)
    full_name = models.CharField(max_length=255)
    consent_given = models.BooleanField(default=False)
    consent_given_at = models.DateTimeField(null=True, blank=True)

    completed_screenings_count = models.PositiveIntegerField(default=0)
    feedback_status = models.CharField(
        max_length=32,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.teacher_id} — {self.full_name}"


class AnalysisRequest(models.Model):
    class ResilienceLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    teacher_profile = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="analysis_requests",
        null=True,
        blank=True,
    )

    teacher_id = models.CharField(max_length=128)
    student_id = models.CharField(max_length=128)
    student_age = models.PositiveSmallIntegerField()
    student_gender = models.CharField(max_length=64)

    scores = models.JSONField(
        help_text="Dict of factor_key -> list/dict of scores (0/1/2/NA)",
    )

    profile = models.JSONField(
        blank=True,
        default=dict,
        help_text="Dict of factor_key -> low/medium/high",
    )

    recommendations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request {self.pk} — teacher {self.teacher_id}, student {self.student_id}"


class TeacherAppFeedback(models.Model):
    teacher_profile = models.OneToOneField(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="app_feedback",
    )

    responses = models.JSONField(default=dict)
    comments = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback — {self.teacher_profile.teacher_id}"