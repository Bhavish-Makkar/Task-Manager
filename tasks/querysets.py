from .models import Task
from django.db.models import Count


def assigned_tasks_for(user):
    """Return only tasks assigned to the given user, with display relations loaded."""
    return (
        Task.objects.assigned_to_user(user)
        .select_related("project", "assigned_to")
        .order_by("due_date")
    )


def overdue_tasks_for(user, today=None):
    return (
        Task.objects.assigned_to_user(user)
        .overdue(today=today)
        .select_related("project", "assigned_to")
        .order_by("due_date")
    )


def group_tasks_by_status(tasks):
    groups = {status: [] for status, _label in Task.Status.choices}
    for task in tasks:
        groups.setdefault(task.status, []).append(task)
    return groups


def status_counts_for_project(project):
    return Task.objects.filter(project=project).values("status").annotate(count=Count("id")).order_by("status")
