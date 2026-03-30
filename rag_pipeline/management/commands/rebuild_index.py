from django.core.management.base import BaseCommand

from rag_pipeline.models import Document, EmbeddingStatus
from rag_pipeline.retrieval.container import get_vector_store


class Command(BaseCommand):
    help = "Drop and rebuild the entire FAISS index from all documents in PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--status",
            choices=[s.value for s in EmbeddingStatus],
            help="Only reindex documents with this status (default: all)",
        )

    def handle(self, **options):
        store = get_vector_store()

        queryset = Document.objects.all()
        if options["status"]:
            queryset = queryset.filter(embedding_status=options["status"])

        documents = list(queryset)
        if not documents:
            self.stdout.write("No documents to index.")
            return

        total_chunks = 0
        for doc in documents:
            count = store.reindex_document(doc)
            total_chunks += count
            self.stdout.write(f"  Indexed document {doc.pk} ({count} chunks)")

        self.stdout.write(self.style.SUCCESS(f"Done. Indexed {total_chunks} chunks across {len(documents)} documents."))
