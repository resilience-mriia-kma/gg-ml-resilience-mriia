import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from django.db import transaction

from .models import AnalysisRequest
from .notifications import NotificationService, queue_report_ready_notification
from .protocols import IRecommendationService

logger = logging.getLogger(__name__)


class AsyncRecommendationService:
    def __init__(self, recommendation_service: IRecommendationService) -> None:
        self.recommendation_service = recommendation_service
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def generate_recommendations_async(self, analysis_request_id: int, scores: dict) -> str | None:
        try:
            logger.info(f"Starting async recommendation generation for request {analysis_request_id}")

            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.recommendation_service.get_recommendations_with_sources, scores
            )

            if result.recommendations:
                await self._update_analysis_request(analysis_request_id, result.recommendations, result.sources)
                await self._send_report_notification(analysis_request_id)

                logger.info(f"Successfully generated recommendations for request {analysis_request_id}")
                return result.recommendations
            else:
                logger.warning(f"Empty recommendations generated for request {analysis_request_id}")
                return None

        except Exception as e:
            logger.exception(f"Failed to generate recommendations for request {analysis_request_id}: {e}")
            await self._mark_recommendation_failed(analysis_request_id, str(e))
            return None

    async def _update_analysis_request(self, analysis_request_id: int, recommendations: str, sources: list) -> None:
        def update_db():
            with transaction.atomic():
                AnalysisRequest.objects.filter(pk=analysis_request_id).update(
                    recommendations=recommendations,
                    sources=sources
                )

        await asyncio.get_event_loop().run_in_executor(self.executor, update_db)

    async def _mark_recommendation_failed(self, analysis_request_id: int, error_message: str) -> None:
        def update_db():
            with transaction.atomic():
                # For now, just leave recommendations empty
                # In the future, we could add a status field to track failures
                AnalysisRequest.objects.filter(pk=analysis_request_id).update(
                    recommendations="# Рекомендації недоступні\n\nВиникла помилка під час генерації рекомендацій. Будь ласка, зверніться до адміністратора."
                )

        await asyncio.get_event_loop().run_in_executor(self.executor, update_db)

    async def _send_report_notification(self, analysis_request_id: int) -> None:
        """
        Send report ready notification once recommendations are generated.

        This notification includes the completed recommendations and is sent only
        after the background processing is complete.
        """
        def send_notification():
            try:
                analysis_request = AnalysisRequest.objects.get(pk=analysis_request_id)

                # Verify that recommendations are actually available before notifying
                if not analysis_request.recommendations.strip():
                    logger.warning(f"Attempted to send report notification for request {analysis_request_id} but recommendations are empty")
                    return

                notification_service = NotificationService()
                report_notification = queue_report_ready_notification(analysis_request)

                if report_notification:
                    notification_service.send(report_notification)
                    logger.info(f"Report ready notification sent successfully for request {analysis_request_id}")
                else:
                    logger.warning(f"No report notification queued for request {analysis_request_id} (likely missing email)")

            except AnalysisRequest.DoesNotExist:
                logger.error(f"AnalysisRequest {analysis_request_id} not found when sending report notification")
            except Exception as e:
                logger.exception(f"Failed to send report notification for request {analysis_request_id}: {e}")

        await asyncio.get_event_loop().run_in_executor(self.executor, send_notification)

    def start_background_task(self, analysis_request_id: int, scores: dict) -> asyncio.Task:
        task = asyncio.create_task(self.generate_recommendations_async(analysis_request_id, scores))
        task.add_done_callback(
            lambda t: logger.info(f"Background recommendation task completed for request {analysis_request_id}")
        )

        return task
