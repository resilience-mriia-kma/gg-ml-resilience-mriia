from django.urls import path

from rag_pipeline import views

urlpatterns = [
    path("query/", views.query, name="rag_query"),
]
