from django.urls import path

from . import views
from .views import (
    AnalysisFormView,
    AnalysisProcessingView,
    AnalysisReportView,
    TeacherConsentView,
    TeacherFeedbackDeclineView,
    TeacherFeedbackFormView,
    TeacherFeedbackView,
    TeacherInfoSheetView,
)

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", AnalysisFormView.as_view(), name="analysis_form"),
    path("analyze/processing/<int:pk>/", AnalysisProcessingView.as_view(), name="analysis_processing"),
    path("reports/<int:pk>/", AnalysisReportView.as_view(), name="analysis_report"),
    path("feedback/", TeacherFeedbackView.as_view(), name="feedback_form"),
    path("teacher-info/", TeacherInfoSheetView.as_view(), name="teacher_info_sheet"),
    path("teacher-consent/", TeacherConsentView.as_view(), name="teacher_consent"),
    path("teacher-feedback/", TeacherFeedbackFormView.as_view(), name="teacher_feedback_form"),
    path(
        "teacher-feedback-decline/",
        TeacherFeedbackDeclineView.as_view(),
        name="teacher_feedback_decline",
    ),
]
