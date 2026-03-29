from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "has_embedding", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(boolean=True, description="Embedding")
    def has_embedding(self, obj):
        return obj.embedding is not None
