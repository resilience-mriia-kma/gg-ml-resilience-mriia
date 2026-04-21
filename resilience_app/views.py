import hashlib

from dependency_injector.wiring import Provide, inject
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .constants import FACTORS, FEEDBACK_TRIGGER_COUNT, ID_FIELDS, TEACHER_APP_FEEDBACK_SECTIONS
from .container import ResilienceContainer
from .forms import AnalysisRequestForm, TeacherAppFeedbackForm, TeacherConsentForm, TeacherFeedbackForm
from .models import AnalysisRequest, TeacherAppFeedback, TeacherFeedback, TeacherProfile
from .notifications import queue_feedback_request_if_needed, queue_report_ready_notification
from .recommendation_service import RecommendationService
from .scoring import compute_profile


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:16]


def index(request):
    return JsonResponse({"status": "ok", "message": "ml-resilience-mriia"})


def _get_active_teacher(request):
    teacher_profile_id = request.session.get("teacher_profile_id")
    if not teacher_profile_id:
        return None

    try:
        return TeacherProfile.objects.get(id=teacher_profile_id, consent_given=True)
    except TeacherProfile.DoesNotExist:
        return None


def _restore_teacher_session(request, teacher_profile):
    request.session["teacher_profile_id"] = teacher_profile.pk
    request.session["teacher_id"] = teacher_profile.teacher_id
    request.session["teacher_full_name"] = teacher_profile.full_name
    if teacher_profile.teacher_email:
        request.session["teacher_email"] = teacher_profile.teacher_email
    request.session.modified = True


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
        recommendation_service: RecommendationService = Provide[ResilienceContainer.recommendation_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.recommendation_service = recommendation_service

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        form = AnalysisRequestForm(initial=self._get_initial_data(teacher_profile))
        return self._render(request, teacher_profile, form)

    def post(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        form = AnalysisRequestForm(request.POST, initial_teacher_id=teacher_profile.teacher_id)
        if not form.is_valid():
            return self._render(request, teacher_profile, form)

        scores = {key: form.get_scores(key) for key in FACTORS}
        profile = compute_profile(scores)
        recommendations = self.recommendation_service.get_recommendations(scores)

        analysis_request = AnalysisRequest.objects.create(
            teacher_profile=teacher_profile,
            teacher_id=teacher_profile.teacher_id,
            teacher_email=teacher_profile.teacher_email or "",
            student_id=form.cleaned_data["student_id"],
            student_age=form.cleaned_data["student_age"],
            student_gender=form.cleaned_data["student_gender"],
            scores=scores,
            profile=profile,
            recommendations=recommendations,
        )

        queue_report_ready_notification(analysis_request)
        queue_feedback_request_if_needed(analysis_request)

        TeacherProfile.objects.filter(pk=teacher_profile.pk).update(
            completed_screenings_count=F("completed_screenings_count") + 1
        )
        teacher_profile.refresh_from_db()
        _restore_teacher_session(request, teacher_profile)

        request.session["analysis_success_message"] = (
            "Відповіді успішно зафіксовано. RAG-звіт буде надіслано на електронну пошту."
        )

        fresh_form = AnalysisRequestForm(initial=self._get_initial_data(teacher_profile))
        return self._render(request, teacher_profile, fresh_form, success=True)

    def _render(self, request, teacher_profile, form, *, success=False):
        success_message = request.session.pop("analysis_success_message", None)
        feedback_message = request.session.pop("feedback_message", None)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "teacher_profile": teacher_profile,
                "teacher_full_name": teacher_profile.full_name,
                "id_fields": [form[name] for name in ID_FIELDS],
                "factor_groups": self._group_factor_fields(form),
                "success": success,
                "success_message": success_message,
                "feedback_message": feedback_message,
                "show_feedback_offer": _feedback_should_be_offered(teacher_profile),
                "completed_screenings_count": teacher_profile.completed_screenings_count,
            },
        )

    def _group_factor_fields(self, form):
        groups = []
        for factor_key, factor in FACTORS.items():
            fields = []
            for item in factor["items"]:
                field_name = f"{factor_key}_{item['id']}"
                fields.append(
                    {
                        "id": item["id"],
                        "text": item["text"],
                        "field": form[field_name],
                    }
                )
            groups.append({"label": factor["label"], "fields": fields})
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
                "value": analysis_request.profile.get(factor_key, "-"),
            }
            for factor_key in FACTORS
        ]

        recommendation_lines = [
            line.strip()
            for line in analysis_request.recommendations.splitlines()
            if line.strip()
        ]

        return render(
            request,
            self.template_name,
            {
                "analysis_request": analysis_request,
                "profile_rows": profile_rows,
                "recommendation_lines": recommendation_lines,
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
        form = TeacherFeedbackForm(
            initial={
                "teacher_id": request.GET.get("teacher_id", ""),
                "teacher_email": request.GET.get("teacher_email", ""),
                "forms_completed": request.GET.get("forms_completed", 0),
            }
        )
        return self._render(request, form)

    def post(self, request):
        form = TeacherFeedbackForm(request.POST)
        if not form.is_valid():
            return self._render(request, form)

        TeacherFeedback.objects.create(
            teacher_id=form.cleaned_data["teacher_id"],
            teacher_email=form.cleaned_data["teacher_email"],
            forms_completed=form.cleaned_data["forms_completed"],
            rating=int(form.cleaned_data["rating"]),
            comments=form.cleaned_data["comments"],
        )

        return self._render(request, TeacherFeedbackForm(), success=True)


class TeacherInfoSheetView(View):
    template_name = "resilience_app/teacher_info_sheet.html"

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if teacher_profile:
            return redirect("analysis_form")
        return render(request, self.template_name)


class TeacherConsentView(View):
    template_name = "resilience_app/teacher_consent.html"

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if teacher_profile:
            return redirect("analysis_form")

        email = request.GET.get("email", "").strip()
        teacher_id = _hash_email(email) if email else ""

        if email:
            request.session["teacher_email"] = email
            request.session.modified = True

        form = TeacherConsentForm(initial={"teacher_id": teacher_id})
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "email_prefilled": bool(email),
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
        teacher_email = request.session.get("teacher_email", "").strip()

        teacher_profile = TeacherProfile.objects.filter(teacher_id=teacher_id).first()

        if teacher_profile and teacher_profile.consent_given:
            teacher_profile.full_name = full_name
            if teacher_email:
                teacher_profile.teacher_email = teacher_email
            teacher_profile.save(update_fields=["full_name", "teacher_email", "updated_at"])
        else:
            teacher_profile, _ = TeacherProfile.objects.get_or_create(
                teacher_id=teacher_id,
                defaults={
                    "full_name": full_name,
                    "teacher_email": teacher_email or None,
                },
            )
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
            "Ви відмовилися від заповнення форми оцінки застосунку. Основний опитувальник залишається доступним."
        )
        return redirect("analysis_form")


class TeacherFeedbackFormView(View):
    template_name = "resilience_app/teacher_feedback_form.html"

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        feedback = getattr(teacher_profile, "app_feedback", None)
        form = TeacherAppFeedbackForm(initial=self._build_initial(feedback) if feedback else None)
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

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "teacher_profile": teacher_profile,
                "feedback_groups": self._group_feedback_fields(form),
                "already_submitted": True,
                "success": True,
            },
        )

    def _group_feedback_fields(self, form):
        groups = []
        for _, section in TEACHER_APP_FEEDBACK_SECTIONS.items():
            fields = []
            for field_def in section["fields"]:
                fields.append(
                    {
                        "name": field_def["name"],
                        "text": field_def["label"],
                        "field": form[field_def["name"]],
                    }
                )
            groups.append({"label": section["label"], "fields": fields})
        return groups

    def _build_initial(self, feedback):
        initial = {"comments": feedback.comments}
        for _, section_data in feedback.responses.items():
            for field_name, value in section_data.items():
                initial[field_name] = value
        return initial
