from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils import timezone

from .constants import FACTORS, RESILIENCE_LEVEL_UKRAINIAN
from .models import AnalysisRequest, Notification, TeacherProfile
from .teacher_ids import normalize_teacher_email

logger = logging.getLogger(__name__)


def enqueue_notification(
    *,
    notification_type: str,
    recipient_email: str,
    subject: str,
    context: dict | None = None,
    analysis_request: AnalysisRequest | None = None,
    attachment_path: str = "",
    dedupe_key: str | None = None,
    scheduled_at=None,
) -> Notification:
    defaults = {
        "analysis_request": analysis_request,
        "type": notification_type,
        "recipient_email": recipient_email,
        "subject": subject,
        "context": context or {},
        "attachment_path": attachment_path,
        "scheduled_at": scheduled_at or timezone.now(),
    }

    if dedupe_key:
        notification, _ = Notification.objects.get_or_create(
            dedupe_key=dedupe_key,
            defaults=defaults,
        )
        return notification

    return Notification.objects.create(**defaults)


def queue_consent_form_notification(
    *,
    teacher_profile: TeacherProfile,
) -> Notification:
    normalized_email = normalize_teacher_email(teacher_profile.teacher_email)
    if not normalized_email:
        raise ValueError("Teacher profile must have an email address")

    context = {
        "teacher_id": teacher_profile.teacher_id,
        "teacher_email": normalized_email,
    }

    dedupe_key = f"consent_form:{teacher_profile.teacher_id}"

    return enqueue_notification(
        notification_type=Notification.NotificationType.CONSENT_FORM,
        recipient_email=normalized_email,
        subject="Згода та форма оцінювання резильєнтності",
        context=context,
        attachment_path=settings.CONSENT_DOCUMENT_PATH,
        dedupe_key=dedupe_key,
    )


def queue_report_ready_notification(
    analysis_request: AnalysisRequest,
) -> Notification | None:
    if not analysis_request.teacher_email or not analysis_request.teacher_email.strip():
        logger.warning(
            "Skipping report notification for analysis_request %s - no email address",
            analysis_request.pk,
        )
        return None

    return enqueue_notification(
        notification_type=Notification.NotificationType.REPORT_READY,
        recipient_email=analysis_request.teacher_email,
        subject=f"Готовий звіт для учня {analysis_request.student_id}",
        context={
            "analysis_request_id": analysis_request.pk,
            "teacher_id": analysis_request.teacher_id,
            "teacher_email": analysis_request.teacher_email,
        },
        analysis_request=analysis_request,
        dedupe_key=f"report_ready:{analysis_request.pk}",
    )


def queue_feedback_request_if_needed(
    analysis_request: AnalysisRequest,
) -> Notification | None:
    if not analysis_request.teacher_email or not analysis_request.teacher_email.strip():
        return None

    completed_forms = AnalysisRequest.objects.filter(
        teacher_id=analysis_request.teacher_id,
    ).count()

    if completed_forms % 10 != 0:
        return None

    return enqueue_notification(
        notification_type=Notification.NotificationType.FEEDBACK_REQUEST,
        recipient_email=analysis_request.teacher_email,
        subject="Поділіться коротким фідбеком про систему",
        context={
            "teacher_id": analysis_request.teacher_id,
            "teacher_email": analysis_request.teacher_email,
            "forms_completed": completed_forms,
        },
        analysis_request=analysis_request,
        dedupe_key=f"feedback_request:{analysis_request.teacher_id}:{completed_forms}",
    )


class NotificationService:
    def __init__(self):
        self.handlers = {
            Notification.NotificationType.CONSENT_FORM: self._send_consent_form,
            Notification.NotificationType.REPORT_READY: self._send_report_ready,
            Notification.NotificationType.FEEDBACK_REQUEST: self._send_feedback_request,
        }

    def send(self, notification: Notification) -> None:
        handler = self.handlers.get(notification.type)
        if handler is None:
            notification.mark_failed(f"Unknown notification type: {notification.type}")
            return

        try:
            handler(notification)
            notification.mark_sent()
        except Exception as exc:
            logger.exception("Failed to send notification %s", notification.pk)
            notification.mark_failed(str(exc))

    def _send_consent_form(self, notification: Notification) -> None:
        context = notification.context

        # Check if custom teacher info URL is provided (from admin action)
        if "teacher_info_url" in context:
            target_url = context["teacher_info_url"]
            body = (
                "Вітаємо!\n\n"
                "Запрошуємо Вас взяти участь у дослідженні стійкості учнів.\n\n"
                f"Для початку перейдіть за посиланням: {target_url}\n\n"
                "Після заповнення форми готовий звіт буде надіслано на цю адресу.\n"
                "Дякуємо за участь у дослідженні!\n"
            )
        else:
            # Original consent form flow
            target_url = self._absolute_url(
                reverse("teacher_consent"),
                query_params={"teacher_id": context["teacher_id"]},
            )
            body = (
                "Вітаємо!\n\n"
                "Просимо ознайомитись з інформаційним листом та надати згоду на участь у дослідженні.\n\n"
                f"Посилання: {target_url}\n\n"
                "У вкладенні додано документ зі згодою.\n"
                "Після заповнення форми готовий звіт буде надіслано на цю адресу.\n"
            )

        self._send_email(
            subject=notification.subject,
            body=body,
            recipient_email=notification.recipient_email,
            attachment_path=notification.attachment_path,
        )

    def _send_report_ready(self, notification: Notification) -> None:
        analysis_request = notification.analysis_request
        if analysis_request is None:
            raise ValueError("Report notification requires analysis_request")

        report_url = self._absolute_url(
            reverse("analysis_report", kwargs={"pk": analysis_request.pk})
        )

        summary_lines = []
        for factor_key, factor in FACTORS.items():
            raw_value = analysis_request.profile.get(factor_key, '')
            ukrainian_value = RESILIENCE_LEVEL_UKRAINIAN.get(raw_value, raw_value or '-')
            summary_lines.append(
                f"- {factor['label']}: {ukrainian_value}"
            )

        recommendation_lines = self._extract_recommendation_lines(
            analysis_request.recommendations,
            limit=5,
        )
        recommendation_block = (
            "\n".join(f"- {line}" for line in recommendation_lines)
            if recommendation_lines
            else "- Рекомендації будуть доступні у повному звіті."
        )

        body = (
            "Ваш звіт готовий.\n\n"
            "Короткий summary по факторах:\n"
            f"{chr(10).join(summary_lines)}\n\n"
            "Ключові рекомендації:\n"
            f"{recommendation_block}\n\n"
            f"Повний звіт: {report_url}\n"
        )

        self._send_email(
            subject=notification.subject,
            body=body,
            recipient_email=notification.recipient_email,
        )

        if analysis_request.report_emailed_at is None:
            analysis_request.report_emailed_at = timezone.now()
            analysis_request.save(update_fields=["report_emailed_at"])

    def _send_feedback_request(self, notification: Notification) -> None:
        context = notification.context

        feedback_url = self._absolute_url(
            reverse("teacher_feedback_form"),
            query_params={"teacher_id": context["teacher_id"]},
        )

        body = (
            "Дякуємо за використання системи.\n\n"
            f"Ви вже заповнили {context['forms_completed']} форм.\n"
            "Будь ласка, залиште короткий фідбек про зручність системи:\n"
            f"{feedback_url}\n"
        )

        self._send_email(
            subject=notification.subject,
            body=body,
            recipient_email=notification.recipient_email,
        )

    def _send_email(
        self,
        *,
        subject: str,
        body: str,
        recipient_email: str,
        attachment_path: str = "",
    ) -> None:
        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )

        if attachment_path:
            file_path = Path(attachment_path)
            if file_path.exists() and file_path.is_file():
                message.attach_file(file_path)

        message.send(fail_silently=False)

    def _absolute_url(self, path: str, query_params: dict | None = None) -> str:
        base = settings.APP_BASE_URL.rstrip("/")
        url = f"{base}{path}"
        if query_params:
            url = f"{url}?{urlencode(query_params)}"
        return url

    def _extract_recommendation_lines(
        self,
        recommendations: str,
        *,
        limit: int = 5,
    ) -> list[str]:
        lines = []
        for raw_line in recommendations.splitlines():
            line = raw_line.strip().lstrip("-").lstrip("•").strip()
            if not line:
                continue
            lines.append(line)
            if len(lines) >= limit:
                break
        return lines
