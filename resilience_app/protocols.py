from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .recommendation_service import RecommendationResult


class IRecommendationService(Protocol):
    def get_recommendations(self, scores: dict) -> str: ...
    def get_recommendations_with_sources(self, scores: dict) -> "RecommendationResult": ...
