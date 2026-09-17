from .models import Task


def assigned_tasks_for(user):
    """Return only tasks assigned to the given user, with display relations loaded."""
    return (
        Task.objects.filter(assigned_to=user)
        .select_related("project", "assigned_to")
        .order_by("due_date")
    )
