from django.contrib.auth.models import User
from django.db import models

from projects.models import Project


class TaskQuerySet(models.QuerySet):
    def assigned_to_user(self, user):
        return self.filter(assigned_to=user)

    def overdue(self, today=None):
        from django.utils import timezone

        today = today or timezone.localdate()
        return self.filter(due_date__lt=today).exclude(status=Task.Status.DONE)


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        DONE = "DONE", "Done"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )

    objects = TaskQuerySet.as_manager()

    def __str__(self):
        return self.title

# Create your models here.
