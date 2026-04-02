from django.apps import AppConfig

from rag_pipeline.container import build_rag_container


class RagPipelineConfig(AppConfig):
    name = "rag_pipeline"

    def ready(self):
        self.container = build_rag_container()
        self.container.wire(
            modules=["rag_pipeline.views", "resilience_app.views"],
            packages=["rag_pipeline"],
        )
