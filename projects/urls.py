from django.urls import path

from . import views
from tasks import views as task_views
from comments import views as comment_views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("create/", views.project_create, name="project_create"),
    path("<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("<int:pk>/delete/", views.project_delete, name="project_delete"),
    path("<int:project_id>/tasks/create/", task_views.task_create, name="task_create"),
    path("<int:project_id>/tasks/<int:task_id>/", task_views.task_detail, name="task_detail"),
    path("<int:project_id>/tasks/<int:task_id>/edit/", task_views.task_edit, name="task_edit"),
    path("<int:project_id>/tasks/<int:task_id>/delete/", task_views.task_delete, name="task_delete"),
    path("<int:project_id>/tasks/<int:task_id>/comments/create/", comment_views.comment_create, name="comment_create"),
    path("<int:pk>/", views.project_detail, name="project_detail"),
]
