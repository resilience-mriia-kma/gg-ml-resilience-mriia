import logging
import os

from django.apps import apps
from django.db import transaction

from rag_pipeline.data_ingestion.raw_source_import.chunk_splitter import ChunkSplitter
from rag_pipeline.data_ingestion.raw_source_import.file_importer import FileImporter
from rag_pipeline.models import Document, DocumentChunk, EmbeddingStatus, KnowledgeSource, SourceType

logger = logging.getLogger(__name__)


def run_pipeline(knowledge_source: KnowledgeSource) -> Document:
    """
    Orchestrates the full ingestion flow:
      1. Parse file → list of chunks
      2. Create Document + bulk-create DocumentChunks (atomic)
      3. Embed chunks and add to FAISS index
      4. Link KnowledgeSource to the Document
    """
    file_importer = FileImporter(ChunkSplitter())
    raw_chunks = file_importer.import_file(
        knowledge_source.file.path, resilience_factor=knowledge_source.resilience_factor
    )
    if not raw_chunks:
        raise ValueError("No chunks extracted from file")

    title = os.path.basename(knowledge_source.file.name)

    with transaction.atomic():
        document = Document.objects.create(
            title=title,
            source=SourceType.FILE,
            embedding_status=EmbeddingStatus.PENDING,
        )
        DocumentChunk.objects.bulk_create([
            DocumentChunk(
                document=document,
                content=chunk.content,
                resilience_factor=chunk.resilience_factor,
                token_count=chunk.token_count,
                chunk_index=chunk.chunk_index,
            )
            for chunk in raw_chunks
        ])

    logger.info(
        "Created document %d ('%s') with %d chunks",
        document.pk,
        title,
        len(raw_chunks),
    )

    # Embedding is a network call — keep outside the DB transaction
    vector_store = apps.get_app_config("rag_pipeline").container.vector_store()
    vector_store.index_document(document)
    # index_document delegates status update to DocumentRepository.update_document_status,
    # which sets embedding_status=INDEXED and indexed_at=now() and saves the document in-place.

    knowledge_source.document = document
    knowledge_source.save(update_fields=["document"])

    return document
