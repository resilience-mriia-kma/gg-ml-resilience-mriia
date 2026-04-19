from django.db import models
from django.utils import timezone


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
    teacher_email = models.EmailField()
    student_id = models.CharField(max_length=128)
    student_age = models.PositiveSmallIntegerField()
    student_gender = models.CharField(max_length=64)

    scores = models.JSONField(
        help_text="Dict of factor_key -> list/dict of scores (0/1/2/NA)",
    )

    # Computed profile per factor
    profile = models.JSONField(
        blank=True,
        default=dict,
        help_text="Dict of factor_key -> low/medium/high",
    )
    recommendations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    report_emailed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return (
            f"Request {self.pk} — teacher {self.teacher_id} "
            f"({self.teacher_email}), student {self.student_id}"
        )


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        CONSENT_FORM = "consent_form", "Consent + form"
        REPORT_READY = "report_ready", "Report ready"
        FEEDBACK_REQUEST = "feedback_request", "Feedback request"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    analysis_request = models.ForeignKey(
        AnalysisRequest,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=32, choices=NotificationType.choices)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    context = models.JSONField(default=dict, blank=True)
    attachment_path = models.CharField(max_length=512, blank=True)
    dedupe_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )

    scheduled_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ("scheduled_at", "pk")

    def mark_sent(self):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.error_message = ""
        self.save(update_fields=["status", "sent_at", "error_message"])

    def mark_failed(self, error_message: str):
        self.status = self.Status.FAILED
        self.error_message = error_message[:5000]
        self.save(update_fields=["status", "error_message"])

    def __str__(self):
        return f"Notification {self.pk} — {self.type} to {self.recipient_email}"


class ConsentFormInvitation(models.Model):
    """
    Модель для управління розсилкою запрошень на заповнення форми.
    Зберігає інформацію про вчителів, яким треба надіслати запрошення.
    """
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    # Ідентифікація вчителя
    teacher_id = models.CharField(max_length=128, unique=True)
    teacher_email = models.EmailField()
    full_name = models.CharField(max_length=255, blank=True)

    # Статус розсилки
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Дедублікація - не відправляти повторно
    invitation_sent = models.BooleanField(default=False)

    # Відслідковування
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Consent Form Invitation"
        verbose_name_plural = "Consent Form Invitations"

    def mark_sent(self):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.invitation_sent = True
        self.error_message = ""
        self.save(update_fields=["status", "sent_at", "invitation_sent", "error_message"])

    def mark_failed(self, error_message: str):
        self.status = self.Status.FAILED
        self.error_message = error_message[:5000]
        self.save(update_fields=["status", "error_message"])

    def __str__(self):
        return f"{self.teacher_id} ({self.teacher_email}) — {self.get_status_display()}"


class TeacherFeedback(models.Model):
    teacher_id = models.CharField(max_length=128)
    teacher_email = models.EmailField()
    forms_completed = models.PositiveIntegerField()
    rating = models.PositiveSmallIntegerField()
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return (
            f"Feedback from {self.teacher_id} "
            f"({self.teacher_email}) after {self.forms_completed} forms"
        )
