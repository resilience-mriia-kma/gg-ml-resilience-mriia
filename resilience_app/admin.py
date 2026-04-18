from django.contrib import admin

from .models import AnalysisRequest, TeacherAppFeedback, TeacherProfile


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
        "student_id",
        "student_age",
        "student_gender",
        "created_at",
    )
    search_fields = ("teacher_id", "student_id")
    list_filter = ("created_at", "student_gender")
    readonly_fields = ("created_at",)


@admin.register(TeacherAppFeedback)
class TeacherAppFeedbackAdmin(admin.ModelAdmin):
    list_display = ("teacher_profile", "created_at", "updated_at")
    search_fields = ("teacher_profile__teacher_id", "teacher_profile__full_name")
    readonly_fields = ("created_at", "updated_at")