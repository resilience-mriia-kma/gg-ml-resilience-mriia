from dependency_injector.wiring import Provide, inject
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .constants import FACTORS
from .container import ResilienceContainer
from .forms import AnalysisRequestForm, TeacherFeedbackForm
from .models import AnalysisRequest, TeacherFeedback
from .notifications import (
    queue_feedback_request_if_needed,
    queue_report_ready_notification,
)
from .recommendation_service import RecommendationService
from .scoring import compute_profile

ID_FIELDS = [
    "teacher_id",
    "teacher_email",
    "student_id",
    "student_age",
    "student_gender",
]


def index(request):
    return JsonResponse({"status": "ok", "message": "ml-resilience-mriia"})


class AnalysisFormView(View):
    template_name = "resilience_app/analysis_form.html"

    @inject
    def __init__(
        self,
        recommendation_service: RecommendationService = Provide[
            ResilienceContainer.recommendation_service
        ],
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.recommendation_service = recommendation_service

    def get(self, request):
        form = AnalysisRequestForm(initial=self._get_initial_data(request))
        return self._render(request, form)

    def post(self, request):
        form = AnalysisRequestForm(request.POST)
        if not form.is_valid():
            return self._render(request, form)

        scores = {key: form.get_scores(key) for key in FACTORS}
        profile = compute_profile(scores)
        recommendations = self.recommendation_service.get_recommendations(scores)

        analysis_request = AnalysisRequest.objects.create(
            teacher_id=form.cleaned_data["teacher_id"],
            teacher_email=form.cleaned_data["teacher_email"],
            student_id=form.cleaned_data["student_id"],
            student_age=form.cleaned_data["student_age"],
            student_gender=form.cleaned_data["student_gender"],
            scores=scores,
            profile=profile,
            recommendations=recommendations,
        )

        queue_report_ready_notification(analysis_request)
        queue_feedback_request_if_needed(analysis_request)

        return self._render(
            request,
            AnalysisRequestForm(initial=self._get_initial_data(request)),
            success=True,
        )

    def _render(self, request, form, *, success=False):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "id_fields": [form[name] for name in ID_FIELDS],
                "factor_groups": self._group_factor_fields(form),
                "success": success,
            },
        )

    def _group_factor_fields(self, form):
        groups = []
        for factor_key, factor in FACTORS.items():
            fields = [form[f"{factor_key}_{item}"] for item in factor["items"]]
            groups.append(
                {
                    "label": factor["label"],
                    "items": factor["items"],
                    "fields": fields,
                }
            )
        return groups

    def _get_initial_data(self, request):
        return {
            "teacher_id": request.GET.get("teacher_id", ""),
            "teacher_email": request.GET.get("teacher_email", ""),
            "student_id": request.GET.get("student_id", ""),
            "student_age": request.GET.get("student_age", ""),
            "student_gender": request.GET.get("student_gender", ""),
        }


class AnalysisReportView(View):
    template_name = "resilience_app/report_detail.html"

    def get(self, request, pk: int):
        analysis_request = get_object_or_404(AnalysisRequest, pk=pk)

        profile_rows = [
            {
                "label": FACTORS[factor_key]["label"],
                "value": analysis_request.profile.get(factor_key, "—"),
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

        return self._render(
            request,
            TeacherFeedbackForm(),
            success=True,
        )

    def _render(self, request, form, *, success=False):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "success": success,
            },
        )