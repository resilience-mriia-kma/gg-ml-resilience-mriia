from django.urls import path

from . import views
from .views import AnalysisFormView

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", AnalysisFormView.as_view(), name="analysis_form"),
]
