from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analyze/', views.analysis_form, name='analysis_form'),
]
