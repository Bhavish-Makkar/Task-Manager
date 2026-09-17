from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from projects.permissions import can_view_project
from tasks.models import Task

from .forms import CommentForm


@login_required
def comment_create(request, project_id, task_id):
    task = get_object_or_404(Task.objects.select_related("project"), pk=task_id, project_id=project_id)
    if not can_view_project(request.user, task.project):
        raise PermissionDenied
    if request.method != "POST":
        return redirect("task_detail", project_id=project_id, task_id=task_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        messages.success(request, "Comment added successfully.")
        return redirect("task_detail", project_id=project_id, task_id=task_id)
    return render(request, "tasks/task_detail.html", {"task": task, "comments": task.comments.select_related("author"), "comment_form": form})
