from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.project_create, name="project_create"),
    path("<int:pk>/", views.project_detail, name="project_detail"),
]
