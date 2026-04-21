import logging

from django.contrib import admin

from .apps import RagPipelineConfig
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
        pipeline = RagPipelineConfig.get_container().ingestion_pipeline()
        succeeded = []
        failed = []

        for ks in queryset:
            try:
                pipeline.ingest_knowledge_source(ks)
                succeeded.append(ks.title)
            except Exception as exc:
                logger.exception(f"Failed to process KnowledgeSource id={ks.pk} title={ks.title!r}")
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
    list_display = ("id", "title", "source", "embedding_status", "indexed_at")
    list_editable = ("title",)
    list_display_links = ("id",)
    readonly_fields = ("embedding_status", "indexed_at", "created_at", "updated_at")
    search_fields = ("title",)
    actions = ["embed_selected"]

    @admin.action(description="Embed selected documents (re-index into FAISS)")
    def embed_selected(self, request, queryset):
        vector_store = RagPipelineConfig.get_container().vector_store()
        succeeded = []
        failed = []

        for doc in queryset:
            try:
                count = vector_store.reindex_document(doc)
                succeeded.append(f"{doc.title} ({count} chunks)")
            except Exception as exc:
                logger.exception(f"Failed to embed Document id={doc.pk} title={doc.title!r}")
                failed.append(f"{doc.title!r}: {exc}")

        if succeeded:
            self.message_user(request, f"Embedded: {', '.join(succeeded)}")
        if failed:
            self.message_user(request, f"Failed: {'; '.join(failed)}", level="error")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "resilience_factor", "chunk_index", "token_count")
    list_filter = ("resilience_factor",)
