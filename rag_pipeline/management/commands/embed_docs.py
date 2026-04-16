import os

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

from rag_pipeline.data_ingestion.raw_source_import.chunk_splitter import ChunkSplitter
from rag_pipeline.data_ingestion.raw_source_import.file_importer import FileImporter
from rag_pipeline.models import Document, DocumentChunk, EmbeddingStatus, SourceType


class Command(BaseCommand):
    help = "Parse, chunk, embed and index documents from file paths."

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", type=str, help="Paths to .docx or .pdf files")
        parser.add_argument(
            "--factor",
            type=str,
            default="",
            help="Resilience factor to tag all chunks with (e.g. family_support). "
            "If omitted, the parser attempts heading-based detection.",
        )

    def handle(self, **options):
        container = apps.get_app_config("rag_pipeline").container
        vector_store = container.vector_store()
        file_importer = FileImporter(ChunkSplitter())

        for filepath in options["files"]:
            if not os.path.isfile(filepath):
                self.stderr.write(self.style.ERROR(f"File not found: {filepath}"))
                continue

            self.stdout.write(f"Processing {filepath} ...")

            raw_chunks = file_importer.import_file(filepath, resilience_factor=options["factor"])
            if not raw_chunks:
                self.stderr.write(self.style.WARNING(f"  No chunks extracted from {filepath}"))
                continue

            title = os.path.basename(filepath)

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

            self.stdout.write(f"  Created document {document.pk} with {len(raw_chunks)} chunks")

            vector_store.index_document(document)
            self.stdout.write(self.style.SUCCESS(f"  Embedded and indexed {len(raw_chunks)} chunks"))

        self.stdout.write(self.style.SUCCESS("Done."))
