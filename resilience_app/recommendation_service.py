import logging
import re
from dataclasses import dataclass

from rag_pipeline.protocols import IRAGService

from .constants import FACTORS, RESILIENCE_LEVEL_UKRAINIAN
from .protocols import IRecommendationService

logger = logging.getLogger(__name__)


@dataclass
class RecommendationResult:
    recommendations: str
    sources: list[dict]


class RecommendationService(IRecommendationService):
    def __init__(self, rag_service: IRAGService) -> None:
        self.rag_service = rag_service

    def get_recommendations(self, scores: dict) -> str:
        """Legacy method for backward compatibility - returns only recommendations."""
        result = self.get_recommendations_with_sources(scores)
        return result.recommendations

    def get_recommendations_with_sources(
        self,
        scores: dict,
        profile: dict[str, str] | None = None,
    ) -> RecommendationResult:
        """Get recommendations along with sources."""
        try:
            query = self._build_query(scores, profile)
            rag_response = self.rag_service.answer(query, profile=profile)
            answer = self._normalize_recommendation_text(rag_response.answer)

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
                recommendations=answer,
                sources=sources
            )
        except Exception:
            logger.exception("RAG service failed, saving without recommendations")
            return RecommendationResult(recommendations="", sources=[])

    def _build_query(self, scores: dict, profile: dict[str, str] | None) -> str:
        lines = [f"{FACTORS[key]['label']}: {values}" for key, values in scores.items()]
        profile_lines = [
            f"{FACTORS[key]['label']}: {RESILIENCE_LEVEL_UKRAINIAN.get(level, level)}"
            for key, level in (profile or {}).items()
        ]
        low_factors = self._factor_labels_by_level(profile, "low")
        medium_factors = self._factor_labels_by_level(profile, "medium")
        high_factors = self._factor_labels_by_level(profile, "high")
        target_count = self._recommendation_count(low_factors, medium_factors)

        priority_lines = []
        if low_factors:
            priority_lines.append(f"Пріоритет підтримки: {', '.join(low_factors)}.")
            priority_lines.append(
                "Обов'язково покрий кожен фактор із пріоритету підтримки хоча б в одній рекомендації."
            )
        if profile and profile.get("health") == "low":
            priority_lines.append(
                "Здоров'я має низький рівень, тому одна рекомендація має містити конкретну дію для режиму, "
                "відпочинку, руху, навантаження або емоційного самопочуття."
            )
        if medium_factors:
            priority_lines.append(f"Зони для розвитку/тренування: {', '.join(medium_factors)}.")
        if high_factors:
            priority_lines.append(f"Сильні сторони, які можна використати як ресурс: {', '.join(high_factors)}.")
            priority_lines.append(
                "Для сильних сторін не описуй проблему як уже наявну; пиши лише про підтримку ресурсу "
                "або майбутній моніторинг."
            )

        profile_block = (
            "\n\nПрофіль стійкості учня/учениці:\n" + "\n".join(profile_lines)
            if profile_lines
            else ""
        )
        priority_block = "\n\n" + "\n".join(priority_lines) if priority_lines else ""

        return (
            "Учень/учениця має такі показники факторів стійкості:\n"
            + "\n".join(lines)
            + profile_block
            + priority_block
            + f"\n\nНадай {target_count} практичні рекомендації українською мовою. "
            + "Кожна рекомендація має бути персоналізована під наведений профіль, а не універсальна для всіх. "
            + "Пиши як живий експертний текст: нумеровані абзаци з короткими назвами, без службових полів "
            + "на кшталт 'Для якого профілю', 'Що робити', 'Тривалість' чи 'Як часто'. "
            + "У сам текст природно вплети конкретну дію, перший крок, тривалість, частоту, залучених людей, "
            + "ознаку успіху та умову, коли треба звернутися по допомогу. "
            + "Якщо фактор має високий рівень, використовуй його як ресурс і не описуй як проблему. "
            + "Не пропускай жоден фактор із низьким рівнем."
        )

    def _factor_labels_by_level(self, profile: dict[str, str] | None, level: str) -> list[str]:
        return [
            FACTORS[key]["label"]
            for key, profile_level in (profile or {}).items()
            if profile_level == level and key in FACTORS
        ]

    def _recommendation_count(self, low_factors: list[str], medium_factors: list[str]) -> int:
        if len(low_factors) >= 3:
            return min(5, len(low_factors) + 1)
        if low_factors:
            return max(3, min(5, len(low_factors) + min(len(medium_factors), 2)))
        if medium_factors:
            return min(5, max(3, len(medium_factors)))
        return 3

    def _normalize_recommendation_text(self, answer: str) -> str:
        """Remove headings/sources that are rendered by the report template."""
        normalized = answer.strip()
        normalized = re.sub(r"^\s*Рекомендації\s*\n+", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\n*\s*Джерел[ао]:.*\Z", "", normalized, flags=re.IGNORECASE | re.DOTALL)
        return normalized.strip()
