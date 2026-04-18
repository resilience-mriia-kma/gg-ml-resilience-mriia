from dependency_injector.wiring import Provide, inject
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from .constants import FACTORS
from .container import ResilienceContainer
from .forms import AnalysisRequestForm
from .forms import TeacherConsentForm
from .models import AnalysisRequest
from .protocols import IRecommendationService

ID_FIELDS = ["teacher_id", "student_id", "student_age", "student_gender"]


def index(request):
    return JsonResponse({"status": "ok", "message": "ml-resilience-mriia"})



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
        if not request.session.get("teacher_consent_given"):
            return redirect("teacher_info_sheet")
        return self._render(request, AnalysisRequestForm())

    def post(self, request):
        if not request.session.get("teacher_consent_given"):
            return redirect("teacher_info_sheet")

        form = AnalysisRequestForm(request.POST)
        if not form.is_valid():
            return self._render(request, form)

        scores = {key: form.get_scores(key) for key in FACTORS}
        recommendations = self.recommendation_service.get_recommendations(scores)

        AnalysisRequest.objects.create(
            teacher_id=form.cleaned_data["teacher_id"],
            student_id=form.cleaned_data["student_id"],
            student_age=form.cleaned_data["student_age"],
            student_gender=form.cleaned_data["student_gender"],
            scores=scores,
            recommendations=recommendations,
        )
        return self._render(request, AnalysisRequestForm(), success=True)

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
    

class TeacherInfoSheetView(View):
    template_name = "resilience_app/teacher_info_sheet.html"

    def get(self, request):
        return render(request, self.template_name)


class TeacherConsentView(View):
    template_name = "resilience_app/teacher_consent.html"

    def get(self, request):
        form = TeacherConsentForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = TeacherConsentForm(request.POST)
        if form.is_valid():
            request.session["teacher_consent_given"] = True
            request.session["teacher_full_name"] = form.cleaned_data["full_name"]
            return redirect("analysis_form")

        return render(request, self.template_name, {"form": form})
