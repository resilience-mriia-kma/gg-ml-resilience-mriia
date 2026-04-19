from django.contrib import admin

from .models import AnalysisRequest, Notification, TeacherAppFeedback, TeacherFeedback, TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = (
        "teacher_id",
        "full_name",
        "consent_given",
        "completed_screenings_count",
        "feedback_status",
        "consent_given_at",
    )
    search_fields = ("teacher_id", "full_name")
    list_filter = ("consent_given", "feedback_status")
    readonly_fields = ("created_at", "updated_at", "consent_given_at")


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


@admin.register(TeacherAppFeedback)
class TeacherAppFeedbackAdmin(admin.ModelAdmin):
    list_display = ("teacher_profile", "created_at", "updated_at")
    search_fields = ("teacher_profile__teacher_id", "teacher_profile__full_name")
    readonly_fields = ("created_at", "updated_at")
