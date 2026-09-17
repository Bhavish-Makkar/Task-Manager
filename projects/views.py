from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import Project


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
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(request, "projects/project_detail.html", {"project": project})


@login_required
def project_list(request):
    projects = Project.objects.filter(owner=request.user).select_related("owner")
    return render(request, "projects/project_list.html", {"projects": projects})

# Create your views here.
