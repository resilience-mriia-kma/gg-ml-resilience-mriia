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
            "Учень має наступні показники факторів стійкості:\n"
            + "\n".join(lines)
            + "\n\nЯкі рекомендації ви можете надати для підтримки стійкості цього учня?"
        )
