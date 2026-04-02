from django.apps import AppConfig

from rag_pipeline.container import RAGContainer


class RagPipelineConfig(AppConfig):
    name = "rag_pipeline"
    container = RAGContainer()

    def ready(self):
        self.container.wire(modules=[".views"])
