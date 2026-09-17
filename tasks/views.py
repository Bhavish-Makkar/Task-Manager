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


@login_required
def task_edit(request, project_id, task_id):
    task = get_object_or_404(
        Task.objects.select_related("project"),
        pk=task_id,
        project_id=project_id,
    )
    if task.project.owner_id != request.user.id:
        raise PermissionDenied

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated successfully.")
            return redirect("task_detail", project_id=project_id, task_id=task.pk)
    else:
        form = TaskForm(instance=task)

    return render(request, "tasks/task_form.html", {"form": form, "project": task.project, "task": task})


@login_required
def task_delete(request, project_id, task_id):
    task = get_object_or_404(
        Task.objects.select_related("project"),
        pk=task_id,
        project_id=project_id,
    )
    if task.project.owner_id != request.user.id:
        raise PermissionDenied

    if request.method == "POST":
        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect("project_detail", pk=project_id)

    return render(request, "tasks/task_confirm_delete.html", {"task": task})

# Create your views here.
