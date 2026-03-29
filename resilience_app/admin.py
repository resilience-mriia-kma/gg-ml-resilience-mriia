from django.contrib import admin

from .models import AnalysisRequest, Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'has_embedding', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(boolean=True, description='Embedding')
    def has_embedding(self, obj):
        return obj.embedding is not None


@admin.register(AnalysisRequest)
class AnalysisRequestAdmin(admin.ModelAdmin):
    list_display = ('pk', 'teacher_id', 'student_id', 'student_age', 'created_at')
    search_fields = ('teacher_id', 'student_id')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
