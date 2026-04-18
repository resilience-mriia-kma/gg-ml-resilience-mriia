from django.contrib import admin

from .models import AnalysisRequest, Notification, TeacherFeedback


@admin.register(AnalysisRequest)
class AnalysisRequestAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "teacher_id",
        "teacher_email",
        "student_id",
        "student_age",
        "created_at",
        "report_emailed_at",
    )
    search_fields = ("teacher_id", "teacher_email", "student_id")
    list_filter = ("created_at", "report_emailed_at")
    readonly_fields = ("created_at", "report_emailed_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "type",
        "recipient_email",
        "status",
        "scheduled_at",
        "sent_at",
    )
    search_fields = ("recipient_email", "subject", "dedupe_key")
    list_filter = ("type", "status", "scheduled_at", "sent_at")
    readonly_fields = ("sent_at",)


@admin.register(TeacherFeedback)
class TeacherFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "teacher_id",
        "teacher_email",
        "forms_completed",
        "rating",
        "created_at",
    )
    search_fields = ("teacher_id", "teacher_email")
    list_filter = ("rating", "created_at")
    readonly_fields = ("created_at",)