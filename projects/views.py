from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from .forms import ProjectForm
from .models import Project
from .permissions import can_view_project
from tasks.models import Task
from tasks.querysets import status_counts_for_project


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, "projects/project_form.html", {"form": form})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if not can_view_project(request.user, project):
        raise PermissionDenied
    tasks = project.tasks.select_related("assigned_to").order_by("due_date")
    raw_counts = {row["status"]: row["count"] for row in status_counts_for_project(project)}
    status_counts = [(label, raw_counts.get(value, 0)) for value, label in Task.Status.choices]
    return render(request, "projects/project_detail.html", {"project": project, "tasks": tasks, "status_counts": status_counts})


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id:
        raise PermissionDenied

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, "projects/project_form.html", {"form": form, "project": project})


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner_id != request.user.id:
        raise PermissionDenied

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project deleted successfully.")
        return redirect("project_list")

    return render(request, "projects/project_confirm_delete.html", {"project": project})


@login_required
def project_list(request):
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(tasks__assigned_to=request.user)
    ).select_related("owner").distinct()
    return render(request, "projects/project_list.html", {"projects": projects})

# Create your views here.
