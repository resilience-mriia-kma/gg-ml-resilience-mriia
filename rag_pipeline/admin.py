from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "embedding_status", "indexed_at", "created_at", "updated_at")
    search_fields = ("title",)
    list_filter = ("embedding_status", "created_at")
    readonly_fields = ("created_at", "updated_at", "indexed_at")
