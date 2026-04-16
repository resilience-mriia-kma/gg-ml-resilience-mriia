from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run a retrieval query against the RAG pipeline and print results."

    def add_arguments(self, parser):
        parser.add_argument("question", type=str, help="User question to send to the RAG pipeline")
        parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve (default: 5)")
        parser.add_argument("--no-llm", action="store_true", help="Only show retrieved chunks, skip LLM generation")

    def handle(self, **options):
        container = apps.get_app_config("rag_pipeline").container
        question = options["question"]
        top_k = options["top_k"]

        if options["no_llm"]:
            self._retrieve_only(container, question, top_k)
        else:
            self._full_rag(container, question, top_k)

    def _retrieve_only(self, container, question, top_k):
        retrieval_service = container.retrieval_service()
        results = retrieval_service.retrieve(question, top_k=top_k)

        if not results:
            self.stdout.write(self.style.WARNING("No chunks retrieved."))
            return

        self.stdout.write(self.style.SUCCESS(f"Retrieved {len(results)} chunk(s):\n"))
        for i, r in enumerate(results, 1):
            self.stdout.write(f"--- [{i}] score={r.score:.4f}  doc={r.document_title!r}  chunk_id={r.chunk_id} ---")
            self.stdout.write(r.content)
            self.stdout.write("")

    def _full_rag(self, container, question, top_k):
        rag_service = container.rag_service()
        response = rag_service.answer(question, top_k=top_k)

        self.stdout.write(self.style.SUCCESS("Answer:\n"))
        self.stdout.write(response.answer)
        self.stdout.write("")

        if response.sources:
            self.stdout.write(self.style.SUCCESS(f"\nSources ({len(response.sources)}):"))
            for i, s in enumerate(response.sources, 1):
                self.stdout.write(f"  [{i}] score={s.score:.4f}  doc={s.document_title!r}  chunk_id={s.chunk_id}")
