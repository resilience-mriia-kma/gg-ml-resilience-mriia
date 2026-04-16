import logging

from django.apps import apps
from django.contrib import admin

from .data_ingestion.pipeline import run_pipeline
from .models import Document, DocumentChunk, KnowledgeSource

logger = logging.getLogger(__name__)


@admin.register(KnowledgeSource)
class KnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "resilience_factor", "category", "is_processed", "created_at")
    list_filter = ("resilience_factor", "category", "source_type")
    readonly_fields = ("document", "created_at", "updated_at")
    actions = ["process_selected"]

    @admin.action(description="Process selected sources (parse → embed → index)")
    def process_selected(self, request, queryset):
        succeeded = []
        failed = []

        for ks in queryset:
            try:
                run_pipeline(ks)
                succeeded.append(ks.title)
            except Exception as exc:
                logger.exception("Failed to process KnowledgeSource id=%s title=%r", ks.pk, ks.title)
                failed.append(f"{ks.title!r}: {exc}")

        if succeeded:
            self.message_user(
                request,
                f"Successfully processed {len(succeeded)} source(s): {', '.join(succeeded)}",
            )
        if failed:
            self.message_user(
                request,
                f"Failed to process {len(failed)} source(s): {'; '.join(failed)}",
                level="error",
            )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "embedding_status", "indexed_at")
    readonly_fields = ("embedding_status", "indexed_at", "created_at", "updated_at")
    actions = ["embed_selected"]

    @admin.action(description="Embed selected documents (re-index into FAISS)")
    def embed_selected(self, request, queryset):
        vector_store = apps.get_app_config("rag_pipeline").container.vector_store()
        succeeded = []
        failed = []

        for doc in queryset:
            try:
                count = vector_store.reindex_document(doc)
                succeeded.append(f"{doc.title} ({count} chunks)")
            except Exception as exc:
                logger.exception("Failed to embed Document id=%s title=%r", doc.pk, doc.title)
                failed.append(f"{doc.title!r}: {exc}")

        if succeeded:
            self.message_user(request, f"Embedded: {', '.join(succeeded)}")
        if failed:
            self.message_user(request, f"Failed: {'; '.join(failed)}", level="error")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "resilience_factor", "chunk_index", "token_count")
    list_filter = ("resilience_factor",)
