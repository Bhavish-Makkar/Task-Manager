def can_view_project(user, project):
    """A project is visible to its owner or any current task assignee."""
    if not user.is_authenticated:
        return False
    return project.owner_id == user.id or project.tasks.filter(assigned_to=user).exists()
