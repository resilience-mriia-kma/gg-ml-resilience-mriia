import logging
import os

from rag_pipeline.data_ingestion.raw_source_import.file_importer import FileImporter
from rag_pipeline.models import Document, KnowledgeSource, SourceType
from rag_pipeline.vectorstore.protocols import IDocumentRepository, IVectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Full ingestion flow: parse -> persist -> embed."""

    def __init__(
        self, file_importer: FileImporter, repository: IDocumentRepository, vector_store: IVectorStore
    ) -> None:
        self.file_importer = file_importer
        self.repository = repository
        self.vector_store = vector_store

    def ingest_file(self, filepath: str, *, resilience_factor: str = "") -> Document:
        raw_chunks = self.file_importer.import_file(filepath, resilience_factor=resilience_factor)
        if not raw_chunks:
            raise ValueError(f"No chunks extracted from {filepath}")

        title = os.path.basename(filepath)
        document = self.repository.create_document_with_chunks(title, SourceType.FILE, raw_chunks)

        logger.info(f"Created document {document.pk} ('{title}') with {len(raw_chunks)} chunks")

        self.vector_store.index_document(document)
        return document

    def ingest_knowledge_source(self, knowledge_source: KnowledgeSource) -> Document:
        # delegates to ingest_file, then fixes title and links
        document = self.ingest_file(knowledge_source.file.path, resilience_factor=knowledge_source.resilience_factor)
        document.title = knowledge_source.title
        document.save(update_fields=["title"])

        knowledge_source.document = document
        knowledge_source.save(update_fields=["document"])

        return document
