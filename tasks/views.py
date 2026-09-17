from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project

from .forms import TaskForm
from .models import Task


@login_required
def task_create(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        raise PermissionDenied

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            messages.success(request, "Task created successfully.")
            return redirect("project_detail", pk=project.pk)
    else:
        form = TaskForm()

    return render(request, "tasks/task_form.html", {"form": form, "project": project})


@login_required
def task_detail(request, project_id, task_id):
    task = get_object_or_404(
        Task.objects.select_related("project", "assigned_to"),
        pk=task_id,
        project_id=project_id,
    )
    project = task.project
    if project.owner_id != request.user.id and not project.tasks.filter(assigned_to=request.user).exists():
        raise PermissionDenied
    return render(request, "tasks/task_detail.html", {"task": task})

# Create your views here.
