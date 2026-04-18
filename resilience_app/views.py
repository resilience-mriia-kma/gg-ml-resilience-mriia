from dependency_injector.wiring import Provide, inject
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from .constants import FACTORS, FEEDBACK_TRIGGER_COUNT, ID_FIELDS, TEACHER_APP_FEEDBACK_SECTIONS
from .container import ResilienceContainer
from .forms import AnalysisRequestForm, TeacherAppFeedbackForm, TeacherConsentForm
from .models import AnalysisRequest, TeacherAppFeedback, TeacherProfile
from .protocols import IRecommendationService


def index(request):
    return JsonResponse({"status": "ok", "message": "ml-resilience-mriia"})


def _calculate_factor_level(scores_dict):
    numeric_scores = [int(value) for value in scores_dict.values() if value in {"0", "1", "2"}]

    if not numeric_scores:
        return AnalysisRequest.ResilienceLevel.MEDIUM

    average_score = sum(numeric_scores) / len(numeric_scores)

    if average_score < 0.75:
        return AnalysisRequest.ResilienceLevel.LOW
    if average_score < 1.5:
        return AnalysisRequest.ResilienceLevel.MEDIUM
    return AnalysisRequest.ResilienceLevel.HIGH


def _build_profile(scores):
    profile = {}
    for factor_key, factor_scores in scores.items():
        profile[factor_key] = _calculate_factor_level(factor_scores)
    return profile


def _get_active_teacher(request):
    teacher_profile_id = request.session.get("teacher_profile_id")
    if not teacher_profile_id:
        return None

    try:
        return TeacherProfile.objects.get(id=teacher_profile_id, consent_given=True)
    except TeacherProfile.DoesNotExist:
        return None


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
        recommendation_service: IRecommendationService = Provide[ResilienceContainer.recommendation_service],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.recommendation_service = recommendation_service

    def get(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        form = AnalysisRequestForm(initial_teacher_id=teacher_profile.teacher_id)
        return self._render(request, teacher_profile, form)

    def post(self, request):
        teacher_profile = _get_active_teacher(request)
        if not teacher_profile:
            return redirect("teacher_info_sheet")

        form = AnalysisRequestForm(request.POST, initial_teacher_id=teacher_profile.teacher_id)
        if not form.is_valid():
            return self._render(request, teacher_profile, form)

        scores = {key: form.get_scores(key) for key in FACTORS}
        profile = _build_profile(scores)
        recommendations = self.recommendation_service.get_recommendations(scores)

        AnalysisRequest.objects.create(
            teacher_profile=teacher_profile,
            teacher_id=form.cleaned_data["teacher_id"],
            student_id=form.cleaned_data["student_id"],
            student_age=form.cleaned_data["student_age"],
            student_gender=form.cleaned_data["student_gender"],
            scores=scores,
            profile=profile,
            recommendations=recommendations,
        )

        teacher_profile.completed_screenings_count += 1
        teacher_profile.save(update_fields=["completed_screenings_count", "updated_at"])

        request.session["analysis_success_message"] = (
            "Опитувальник успішно збережено. Ви можете одразу заповнити форму для наступного учня."
        )

        fresh_form = AnalysisRequestForm(initial_teacher_id=teacher_profile.teacher_id)
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
            groups.append(
                {
                    "label": factor["label"],
                    "fields": fields,
                }
            )
        return groups


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

        form = TeacherConsentForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = TeacherConsentForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        teacher_id = form.cleaned_data["teacher_id"]
        full_name = form.cleaned_data["full_name"]

        teacher_profile = TeacherProfile.objects.filter(teacher_id=teacher_id).first()

        if teacher_profile and teacher_profile.consent_given:
            teacher_profile.full_name = full_name
            teacher_profile.save(update_fields=["full_name", "updated_at"])
        else:
            teacher_profile, _ = TeacherProfile.objects.get_or_create(
                teacher_id=teacher_id,
                defaults={"full_name": full_name},
            )
            teacher_profile.full_name = full_name
            teacher_profile.consent_given = True
            if not teacher_profile.consent_given_at:
                teacher_profile.consent_given_at = timezone.now()
            teacher_profile.save()

        request.session["teacher_profile_id"] = teacher_profile.id
        request.session["teacher_id"] = teacher_profile.teacher_id
        request.session["teacher_full_name"] = teacher_profile.full_name

        return redirect("analysis_form")


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
        form = TeacherAppFeedbackForm(
            initial=self._build_initial(feedback) if feedback else None
        )

        return render(
            request,
            self.template_name,
            {
                "form": form,
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

        request.session["feedback_message"] = (
            "Форму оцінки використання ШІ-агента успішно збережено. Ви можете продовжувати заповнювати основний опитувальник."
        )
        return redirect("analysis_form")

    def _group_feedback_fields(self, form):
        groups = []
        for section_key, section in TEACHER_APP_FEEDBACK_SECTIONS.items():
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