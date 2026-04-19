from django.apps import AppConfig, apps

from rag_pipeline.container import RAGContainer


class RagPipelineConfig(AppConfig):
    name = "rag_pipeline"
    container = RAGContainer()

    def ready(self):
        self.container.wire(modules=[".views", ".admin"])

    @staticmethod
    def get_container() -> RAGContainer:
        config: RagPipelineConfig = apps.get_app_config("rag_pipeline")  # type: ignore[assignment]
        return config.container
