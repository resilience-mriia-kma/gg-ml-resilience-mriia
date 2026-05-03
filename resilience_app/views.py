import logging
import re

from dependency_injector.wiring import Provide, inject
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from resilience_app.protocols import IRecommendationService

from .async_recommendation_service import AsyncRecommendationService
from .constants import (
    FACTORS,
    FEEDBACK_TRIGGER_COUNT,
    GENDER_CHOICES,
    ID_FIELDS,
    RESILIENCE_LEVEL_EXPLANATIONS,
    RESILIENCE_LEVEL_UKRAINIAN,
    RESILIENCE_PROFILE_NOTE,
    TEACHER_APP_FEEDBACK_SECTIONS,
)
from .container import ResilienceContainer
from .forms import (
    AnalysisRequestForm,
    TeacherAppFeedbackForm,
    TeacherConsentForm,
    TeacherFeedbackForm,
)
from .models import AnalysisRequest, TeacherAppFeedback, TeacherFeedback, TeacherProfile
from .notifications import NotificationService, queue_feedback_request_if_needed
from .scoring import compute_profile

logger = logging.getLogger(__name__)


def _normalize_recommendation_source_linebreaks(recommendations: str) -> str:
    normalized = recommendations.strip()
    normalized = re.sub(r"^\s*Рекомендації\s*\n+", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\n*\s*Джерел[ао]:.*\Z", "", normalized, flags=re.IGNORECASE | re.DOTALL)
    return normalized.strip()


def index(request):
    return JsonResponse({"status": "ok", "message": "ml-resilience-mriia"})


def _restore_teacher_session(request, teacher_profile):
    request.session["teacher_profile_id"] = teacher_profile.pk
    request.session["teacher_id"] = teacher_profile.teacher_id
    request.session["teacher_full_name"] = teacher_profile.full_name

    if teacher_profile.teacher_email:
        request.session["teacher_email"] = teacher_profile.teacher_email

    request.session.modified = True


def _get_teacher_from_session(request):
    teacher_profile_id = request.session.get("teacher_profile_id")
    if not teacher_profile_id:
        return None

    try:
        return TeacherProfile.objects.get(
            id=teacher_profile_id,
            consent_given=True,
        )
    except TeacherProfile.DoesNotExist:
        return None


def _get_teacher_from_query(request):
    teacher_id = request.GET.get("teacher_id", "").strip()
    if not teacher_id:
        return None

    teacher_profile = TeacherProfile.objects.filter(
        teacher_id=teacher_id,
        consent_given=True,
    ).first()

    if teacher_profile:
        _restore_teacher_session(request, teacher_profile)

    return teacher_profile


def _get_active_teacher(request):
    teacher_profile = _get_teacher_from_session(request)
    if teacher_profile:
        return teacher_profile

    return _get_teacher_from_query(request)


def _feedback_should_be_offered(teacher_profile):
    if not teacher_profile:
        return False

    return (
        teacher_profile.completed_screenings_count >= FEEDBACK_TRIGGER_COUNT
        and teacher_profile.feedback_status == TeacherProfile.FeedbackStatus.PENDING
    )


class AnalysisFormView(View):
    template_name = "resilience_app/analysis_form.html"

    @inject
    def __init__(
        self,
        recommendation_service: IRecommendationService = Provide[
            ResilienceContainer.recommendation_service
        ],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.recommendation_service = recommendation_service
        self.async_recommendation_service = AsyncRecommendationService(
            recommendation_service
        )

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        if request.GET.get("continue") == "1":
            request.session.pop("analysis_success_message", None)

        form = AnalysisRequestForm(initial=self._get_initial_data(teacher_profile))
        return self._render(request, teacher_profile, form)

    def post(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        form = AnalysisRequestForm(
            request.POST,
            initial_teacher_id=teacher_profile.teacher_id,
        )
        if not form.is_valid():
            return self._render(request, teacher_profile, form)

        scores = {key: form.get_scores(key) for key in FACTORS}
        profile = compute_profile(scores)

        # Save AnalysisRequest immediately with empty recommendations
        analysis_request = AnalysisRequest.objects.create(
            teacher_profile=teacher_profile,
            teacher_id=teacher_profile.teacher_id,
            teacher_email=teacher_profile.teacher_email or "",
            student_id=form.cleaned_data["student_id"],
            student_age=form.cleaned_data["student_age"],
            student_gender=form.cleaned_data["student_gender"],
            scores=scores,
            profile=profile,
            recommendations="",
        )

        # Update teacher statistics immediately
        TeacherProfile.objects.filter(pk=teacher_profile.pk).update(
            completed_screenings_count=F("completed_screenings_count") + 1
        )
        teacher_profile.refresh_from_db()
        _restore_teacher_session(request, teacher_profile)

        # Send immediate notifications (before starting background processing)
        self._send_immediate_notifications(analysis_request)

        self.async_recommendation_service.start_background_task(
            analysis_request.pk,
            scores,
            profile,
        )

        return redirect("analysis_processing", pk=analysis_request.pk)

    def _send_immediate_notifications(self, analysis_request: AnalysisRequest) -> None:
        """
        Send notifications that should be sent immediately after form submission.

        This includes:
        - Feedback request notifications (if threshold reached)
        - Processing acknowledgment notifications (if needed in future)

        Note: Report ready notifications are sent separately when recommendations are complete.
        """
        notification_service = NotificationService()

        try:
            # Send feedback notification if the teacher has reached the threshold
            feedback_notification = queue_feedback_request_if_needed(analysis_request)
            if feedback_notification:
                notification_service.send(feedback_notification)
                logger.info(
                    "Feedback notification sent immediately for request %s",
                    analysis_request.pk,
                )

        except Exception as exc:
            logger.exception(
                "Failed to send immediate notifications for request %s: %s",
                analysis_request.pk,
                exc,
            )

    def _render(self, request, teacher_profile, form):
        feedback_message = request.session.pop("feedback_message", None)
        success_message = request.session.get("analysis_success_message")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "teacher_profile": teacher_profile,
                "teacher_full_name": teacher_profile.full_name,
                "id_fields": [form[name] for name in ID_FIELDS],
                "factor_groups": self._group_factor_fields(form),
                "feedback_message": feedback_message,
                "success_message": success_message,
                "show_feedback_offer": _feedback_should_be_offered(teacher_profile),
                "completed_screenings_count": teacher_profile.completed_screenings_count,
            },
        )

    def _group_factor_fields(self, form):
        groups = []
        display_number = 1

        for factor_key, factor in FACTORS.items():
            fields = []

            for item in factor["items"]:
                field_name = f"{factor_key}_{item['id']}"
                fields.append(
                    {
                        "display_number": display_number,
                        "id": item["id"],
                        "text": item["text"],
                        "field": form[field_name],
                    }
                )
                display_number += 1

            groups.append(
                {
                    "label": factor["label"],
                    "fields": fields,
                }
            )

        return groups

    def _get_initial_data(self, teacher_profile):
        return {
            "teacher_id": teacher_profile.teacher_id,
            "teacher_email": teacher_profile.teacher_email or "",
        }


class AnalysisReportView(View):
    template_name = "resilience_app/report_detail.html"

    def get(self, request, pk: int):
        analysis_request = get_object_or_404(AnalysisRequest, pk=pk)

        profile_rows = [
            {
                "label": FACTORS[factor_key]["label"],
                "level": analysis_request.profile.get(factor_key, ""),
                "value": RESILIENCE_LEVEL_UKRAINIAN.get(
                    analysis_request.profile.get(factor_key, ""),
                    "-",
                ),
            }
            for factor_key in FACTORS
        ]

        recommendations = _normalize_recommendation_source_linebreaks(
            analysis_request.recommendations
        )

        recommendation_lines = [
            line.strip()
            for line in recommendations.splitlines()
            if line.strip()
        ]

        unique_sources = {}
        for source in analysis_request.sources:
            doc_title = source.get("document_title", "")
            if (
                doc_title not in unique_sources
                or source.get("score", 0) > unique_sources[doc_title].get("score", 0)
            ):
                unique_sources[doc_title] = source

        grouped_sources = sorted(
            unique_sources.values(),
            key=lambda item: item.get("score", 0),
            reverse=True,
        )

        return render(
            request,
            self.template_name,
            {
                "analysis_request": analysis_request,
                "recommendations": recommendations,
                "profile_rows": profile_rows,
                "level_explanations": [
                    {
                        "level": level,
                        "label": RESILIENCE_LEVEL_UKRAINIAN[level],
                        "description": description,
                    }
                    for level, description in RESILIENCE_LEVEL_EXPLANATIONS.items()
                ],
                "profile_note": RESILIENCE_PROFILE_NOTE,
                "recommendation_lines": recommendation_lines,
                "sources": grouped_sources,
            },
        )


class TeacherFeedbackView(View):
    template_name = "resilience_app/feedback_form.html"

    def _render(self, request, form, *, success=False):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "success": success,
            },
        )

    def get(self, request):
        success = request.session.pop("basic_feedback_success", False)

        form = TeacherFeedbackForm(
            initial={
                "teacher_id": request.GET.get("teacher_id", ""),
                "teacher_email": request.GET.get("teacher_email", ""),
                "forms_completed": request.GET.get("forms_completed", 0),
            }
        )
        return self._render(request, form, success=success)

    def post(self, request):
        form = TeacherFeedbackForm(request.POST)
        if not form.is_valid():
            return self._render(request, form, success=False)

        TeacherFeedback.objects.create(
            teacher_id=form.cleaned_data["teacher_id"],
            teacher_email=form.cleaned_data["teacher_email"],
            forms_completed=form.cleaned_data["forms_completed"],
            rating=int(form.cleaned_data["rating"]),
            comments=form.cleaned_data["comments"],
        )

        request.session["basic_feedback_success"] = True
        return redirect("feedback_form")


class TeacherInfoSheetView(View):
    template_name = "resilience_app/teacher_info_sheet.html"

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if teacher_profile:
            return redirect("analysis_form")

        teacher_id = request.GET.get("teacher_id", "").strip()

        continue_url = reverse("teacher_consent")
        if teacher_id:
            continue_url = f"{continue_url}?teacher_id={teacher_id}"

        context = {
            "continue_url": continue_url,
        }
        return render(request, self.template_name, context)


class TeacherConsentView(View):
    template_name = "resilience_app/teacher_consent.html"

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if teacher_profile:
            return redirect("analysis_form")

        teacher_id = request.GET.get("teacher_id", "").strip()
        if not teacher_id:
            return redirect("teacher_info_sheet")

        teacher_profile = TeacherProfile.objects.filter(teacher_id=teacher_id).first()
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        if teacher_profile.teacher_email:
            request.session["teacher_email"] = teacher_profile.teacher_email
            request.session.modified = True

        form = TeacherConsentForm(initial={"teacher_id": teacher_id})

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "email_prefilled": bool(teacher_profile.teacher_email),
            },
        )

    def post(self, request):
        form = TeacherConsentForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "email_prefilled": False,
                },
            )

        teacher_id = form.cleaned_data["teacher_id"]
        full_name = form.cleaned_data["full_name"]

        teacher_profile = TeacherProfile.objects.filter(teacher_id=teacher_id).first()
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        teacher_email = (
            teacher_profile.teacher_email
            or request.session.get("teacher_email", "")
        ).strip()

        teacher_profile.full_name = full_name
        if teacher_email:
            teacher_profile.teacher_email = teacher_email
        teacher_profile.consent_given = True
        if not teacher_profile.consent_given_at:
            teacher_profile.consent_given_at = timezone.now()
        teacher_profile.save()

        _restore_teacher_session(request, teacher_profile)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "email_prefilled": bool(teacher_email),
                "consent_success": True,
            },
        )


class TeacherFeedbackDeclineView(View):
    def post(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        teacher_profile.feedback_status = TeacherProfile.FeedbackStatus.DECLINED
        teacher_profile.save(update_fields=["feedback_status", "updated_at"])

        request.session["feedback_message"] = (
            "Ви відмовилися від заповнення форми оцінки застосунку. "
            "Основний опитувальник залишається доступним."
        )
        return redirect("analysis_form")


class TeacherFeedbackFormView(View):
    template_name = "resilience_app/teacher_feedback_form.html"

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        feedback = getattr(teacher_profile, "app_feedback", None)
        form = TeacherAppFeedbackForm(
            initial=self._build_initial(feedback) if feedback else None
        )
        success = request.session.pop("feedback_success", False)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "success": success,
                "teacher_profile": teacher_profile,
                "feedback_groups": self._group_feedback_fields(form),
                "already_submitted": feedback is not None,
            },
        )

    def post(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        form = TeacherAppFeedbackForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "success": False,
                    "teacher_profile": teacher_profile,
                    "feedback_groups": self._group_feedback_fields(form),
                    "already_submitted": False,
                },
            )

        responses = form.get_feedback_responses()
        comments = form.cleaned_data["comments"]

        TeacherAppFeedback.objects.update_or_create(
            teacher_profile=teacher_profile,
            defaults={
                "responses": responses,
                "comments": comments,
            },
        )

        teacher_profile.feedback_status = TeacherProfile.FeedbackStatus.SUBMITTED
        teacher_profile.save(update_fields=["feedback_status", "updated_at"])

        request.session["feedback_success"] = True
        return redirect("teacher_feedback_form")

    def _group_feedback_fields(self, form):
        groups = []

        for _, section in TEACHER_APP_FEEDBACK_SECTIONS.items():
            fields = []

            for field_def in section["fields"]:
                field_name = field_def["name"]
                bound_field = form[field_name]
                form_field = form.fields[field_name]

                fields.append(
                    {
                        "name": field_name,
                        "text": field_def["label"],
                        "field": bound_field,
                        "help_text": field_def.get("help_text") or form_field.help_text,
                    }
                )

            groups.append(
                {
                    "label": section["label"],
                    "fields": fields,
                }
            )

        return groups

    def _build_initial(self, feedback):
        initial = {"comments": feedback.comments}

        for _, section_data in feedback.responses.items():
            for field_name, value in section_data.items():
                initial[field_name] = value

        return initial


class AnalysisProcessingView(View):
    template_name = "resilience_app/analysis_processing.html"

    def get(self, request, pk: int):
        analysis_request = get_object_or_404(AnalysisRequest, pk=pk)
        teacher_profile = _get_active_teacher(request)

        if not teacher_profile or analysis_request.teacher_profile != teacher_profile:
            return redirect("teacher_info_sheet")

        gender_display = dict(GENDER_CHOICES).get(
            analysis_request.student_gender,
            analysis_request.student_gender,
        )

        request.session["analysis_success_message"] = (
            "Відповіді успішно зафіксовано. "
            "RAG-звіт буде надіслано на електронну пошту."
        )

        return render(
            request,
            self.template_name,
            {
                "analysis_request": analysis_request,
                "student_id": analysis_request.student_id,
                "student_age": analysis_request.student_age,
                "student_gender_display": gender_display,
                "teacher_email": analysis_request.teacher_email,
            },
        )
