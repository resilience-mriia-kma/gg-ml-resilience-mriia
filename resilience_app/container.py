from dependency_injector import containers, providers

from rag_pipeline.container import RAGContainer

from .recommendation_service import RecommendationService


class ResilienceContainer(containers.DeclarativeContainer):
    rag_container = providers.Container(RAGContainer)

    recommendation_service = providers.Singleton(
        RecommendationService,
        rag_service=rag_container.rag_service,
    )
