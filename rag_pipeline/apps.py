from django.apps import AppConfig

from rag_pipeline.container import RAGContainer


class RagPipelineConfig(AppConfig):
    name = "rag_pipeline"
    container = RAGContainer()

    def ready(self):
        # Wire both views and admin so that @inject decorators resolve correctly.
        # faiss_index / vector_store are constructed lazily on first use — no
        # eager load_or_create() here so that manage.py check works without
        # faiss/numpy being installed in the local dev environment.
        self.container.wire(modules=[".views", ".admin"])
