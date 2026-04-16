import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from rag_pipeline.apps import RagPipelineConfig

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class Command(BaseCommand):
    help = "Parse, chunk, embed and index documents. Defaults to all files in RAW_SOURCES_DIR."

    def add_arguments(self, parser):
        parser.add_argument(
            "files",
            nargs="*",
            type=str,
            help="Paths to .docx or .pdf files. If omitted, scans RAW_SOURCES_DIR.",
        )
        parser.add_argument(
            "--factor",
            type=str,
            default="",
            help="Resilience factor to tag all chunks with (e.g. family_support). "
            "If omitted, the parser attempts heading-based detection.",
        )

    def handle(self, **options):
        files = options["files"] or self._discover_files()
        if not files:
            self.stderr.write(self.style.WARNING("No files to process."))
            return

        pipeline = RagPipelineConfig.get_container().ingestion_pipeline()

        for filepath in files:
            if not os.path.isfile(filepath):
                self.stderr.write(self.style.ERROR(f"File not found: {filepath}"))
                continue

            self.stdout.write(f"Processing {filepath} ...")

            try:
                document = pipeline.ingest_file(filepath, resilience_factor=options["factor"])
            except ValueError as exc:
                self.stderr.write(self.style.WARNING(f"{exc}"))
                continue

            chunk_count = document.chunks.count()
            self.stdout.write(self.style.SUCCESS(f"  Embedded and indexed {chunk_count} chunks"))

        self.stdout.write(self.style.SUCCESS("Done."))

    def _discover_files(self) -> list[str]:
        source_dir = Path(settings.RAW_SOURCES_DIR)
        if not source_dir.is_dir():
            self.stderr.write(self.style.ERROR(f"RAW_SOURCES_DIR not found: {source_dir}"))
            return []

        files = sorted(str(p) for p in source_dir.iterdir() if p.is_file() and p.suffix in SUPPORTED_EXTENSIONS)
        self.stdout.write(f"Discovered {len(files)} file(s) in {source_dir}")
        return files
