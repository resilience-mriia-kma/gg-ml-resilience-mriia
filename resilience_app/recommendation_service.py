import logging

from rag_pipeline.protocols import IRAGService

from .constants import FACTORS
from .protocols import IRecommendationService

logger = logging.getLogger(__name__)


class RecommendationService(IRecommendationService):
    def __init__(self, rag_service: IRAGService) -> None:
        self.rag_service = rag_service

    def get_recommendations(self, scores: dict) -> str:
        try:
            query = self._build_query(scores)
            return self.rag_service.answer(query).answer
        except Exception:
            logger.exception("RAG service failed, saving without recommendations")
            return ""

    def _build_query(self, scores: dict) -> str:
        lines = [f"{FACTORS[key]['label']}: {values}" for key, values in scores.items()]
        return (
            "A student has the following resilience factor scores:\n"
            + "\n".join(lines)
            + "\n\nWhat recommendations can you provide to support this student's resilience?"
        )
