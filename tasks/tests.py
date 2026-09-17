from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from projects.models import Project

from .models import Task


class TaskModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="aman", password="StrongPassword123!")
        self.assignee = User.objects.create_user(username="ravi", password="StrongPassword123!")
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)

    def test_task_can_be_created_with_valid_relationships_and_choices(self):
        task = Task.objects.create(
            title="Build homepage",
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.HIGH,
            due_date=date(2026, 9, 25),
            project=self.project,
            assigned_to=self.assignee,
        )

        self.assertEqual(task.project, self.project)
        self.assertEqual(task.assigned_to, self.assignee)
        self.assertEqual(self.project.tasks.count(), 1)
        self.assertEqual(self.assignee.assigned_tasks.count(), 1)
        self.assertEqual(str(task), "Build homepage")

    def test_task_can_be_unassigned(self):
        task = Task.objects.create(
            title="Create schema",
            due_date=date(2026, 9, 25),
            project=self.project,
        )

        self.assertIsNone(task.assigned_to)

    def test_project_can_have_multiple_tasks(self):
        for title in ("Task One", "Task Two"):
            Task.objects.create(title=title, due_date=date(2026, 9, 25), project=self.project)

        self.assertEqual(self.project.tasks.count(), 2)

    def test_project_deletion_cascades_to_tasks(self):
        task = Task.objects.create(title="Remove me", due_date=date(2026, 9, 25), project=self.project)

        self.project.delete()

        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_assignee_deletion_unassigns_task(self):
        task = Task.objects.create(
            title="Keep task",
            due_date=date(2026, 9, 25),
            project=self.project,
            assigned_to=self.assignee,
        )

        self.assignee.delete()
        task.refresh_from_db()

        self.assertIsNone(task.assigned_to)

# Create your tests here.
