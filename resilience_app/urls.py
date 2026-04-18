from django.urls import path

from . import views
from .views import AnalysisFormView, AnalysisReportView, TeacherFeedbackView

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", AnalysisFormView.as_view(), name="analysis_form"),
    path("reports/<int:pk>/", AnalysisReportView.as_view(), name="analysis_report"),
    path("feedback/", TeacherFeedbackView.as_view(), name="feedback_form"),
]