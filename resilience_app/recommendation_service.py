import logging
from dataclasses import dataclass
from typing import List

from rag_pipeline.protocols import IRAGService

from .constants import FACTORS
from .protocols import IRecommendationService

logger = logging.getLogger(__name__)


@dataclass
class RecommendationResult:
    recommendations: str
    sources: List[dict]


class RecommendationService(IRecommendationService):
    def __init__(self, rag_service: IRAGService) -> None:
        self.rag_service = rag_service

    def get_recommendations(self, scores: dict) -> str:
        """Legacy method for backward compatibility - returns only recommendations."""
        result = self.get_recommendations_with_sources(scores)
        return result.recommendations

    def get_recommendations_with_sources(self, scores: dict) -> RecommendationResult:
        """Get recommendations along with sources."""
        try:
            query = self._build_query(scores)
            rag_response = self.rag_service.answer(query)

            # Convert sources to serializable format
            sources = [
                {
                    "chunk_id": source.chunk_id,
                    "content": source.content[:200] + "..." if len(source.content) > 200 else source.content,
                    "score": round(source.score, 4),
                    "document_title": source.document_title,
                }
                for source in rag_response.sources
            ]

            return RecommendationResult(
                recommendations=rag_response.answer,
                sources=sources
            )
        except Exception:
            logger.exception("RAG service failed, saving without recommendations")
            return RecommendationResult(recommendations="", sources=[])

    def _build_query(self, scores: dict) -> str:
        lines = [f"{FACTORS[key]['label']}: {values}" for key, values in scores.items()]
        return (
            "Учень має наступні показники факторів стійкості:\n"
            + "\n".join(lines)
            + "\n\nЯкі рекомендації ви можете надати для підтримки стійкості цього учня?"
        )
