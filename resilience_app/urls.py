from django.urls import path

from . import views
from .views import (
    AnalysisFormView,
    TeacherConsentView,
    TeacherFeedbackDeclineView,
    TeacherFeedbackFormView,
    TeacherInfoSheetView,
)

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", AnalysisFormView.as_view(), name="analysis_form"),
    path("teacher-info/", TeacherInfoSheetView.as_view(), name="teacher_info_sheet"),
    path("teacher-consent/", TeacherConsentView.as_view(), name="teacher_consent"),
    path("teacher-feedback/", TeacherFeedbackFormView.as_view(), name="teacher_feedback_form"),
    path(
        "teacher-feedback-decline/",
        TeacherFeedbackDeclineView.as_view(),
        name="teacher_feedback_decline",
    ),
]