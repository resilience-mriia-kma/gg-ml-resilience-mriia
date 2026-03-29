from django.contrib import admin

from .models import AnalysisRequest


@admin.register(AnalysisRequest)
class AnalysisRequestAdmin(admin.ModelAdmin):
    list_display = ('pk', 'teacher_id', 'student_id', 'student_age', 'created_at')
    search_fields = ('teacher_id', 'student_id')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
