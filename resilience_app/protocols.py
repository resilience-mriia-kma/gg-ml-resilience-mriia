from typing import Protocol


class IRecommendationService(Protocol):
    def get_recommendations(self, scores: dict) -> str: ...
