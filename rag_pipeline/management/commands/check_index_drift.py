import numpy as np
from django.core.management.base import BaseCommand

from rag_pipeline.apps import RagPipelineConfig


class Command(BaseCommand):
    help = "Detect and optionally repair drift between FAISS index and PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument("--repair", action="store_true", help="Auto-repair detected drift")

    def handle(self, **options):
        container = RagPipelineConfig.get_container()
        index = container.faiss_index()
        repo = container.repository()

        pg_ids = repo.get_all_chunk_ids()
        faiss_ids = set(index.get_all_ids().tolist())

        orphaned_in_faiss = faiss_ids - pg_ids
        missing_from_faiss = pg_ids - faiss_ids

        if not orphaned_in_faiss and not missing_from_faiss:
            self.stdout.write(self.style.SUCCESS("No drift detected."))
            return

        if orphaned_in_faiss:
            self.stdout.write(
                self.style.WARNING(f"{len(orphaned_in_faiss)} orphaned vectors in FAISS (chunk deleted from DB)")
            )
        if missing_from_faiss:
            self.stdout.write(self.style.WARNING(f"{len(missing_from_faiss)} chunks in DB missing from FAISS"))

        if not options["repair"]:
            self.stdout.write("Run with --repair to fix.")
            return

        if orphaned_in_faiss:
            index.remove(np.array(list(orphaned_in_faiss), dtype=np.int64))
            index.save()
            self.stdout.write(self.style.SUCCESS(f"Removed {len(orphaned_in_faiss)} orphaned vectors from FAISS."))

        if missing_from_faiss:
            count = repo.mark_documents_stale(missing_from_faiss)
            self.stdout.write(self.style.SUCCESS(f"Marked {count} documents as STALE for re-indexing."))
