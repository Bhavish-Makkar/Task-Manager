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

    def test_overdue_query_matches_date_and_status_rules(self):
        today = date(2026, 9, 17)
        overdue_todo = Task.objects.create(title="Old todo", status=Task.Status.TODO, due_date=date(2026, 9, 15), project=self.project, assigned_to=self.assignee)
        overdue_progress = Task.objects.create(title="Old progress", status=Task.Status.IN_PROGRESS, due_date=date(2026, 9, 16), project=self.project, assigned_to=self.assignee)
        Task.objects.create(title="Old done", status=Task.Status.DONE, due_date=date(2026, 9, 15), project=self.project, assigned_to=self.assignee)
        Task.objects.create(title="Today", status=Task.Status.TODO, due_date=today, project=self.project, assigned_to=self.assignee)
        Task.objects.create(title="Future", status=Task.Status.TODO, due_date=date(2026, 9, 18), project=self.project, assigned_to=self.assignee)

        self.assertEqual(list(Task.objects.overdue(today=today)), [overdue_todo, overdue_progress])

    def test_assigned_task_queryset_loads_forward_relations_in_one_query(self):
        for index in range(20):
            Task.objects.create(title=f"Task {index}", due_date=date(2026, 9, 25), project=self.project, assigned_to=self.assignee)

        with self.assertNumQueries(1):
            tasks = list(Task.objects.assigned_to_user(self.assignee).select_related("project", "assigned_to"))

        self.assertEqual(len(tasks), 20)
        self.assertEqual(tasks[0].project.name, "Website Redesign")
        self.assertEqual(tasks[0].assigned_to.username, "ravi")

    def test_status_counts_are_grouped_by_database(self):
        from .querysets import status_counts_for_project
        for index in range(2):
            Task.objects.create(title=f"Todo {index}", status=Task.Status.TODO, due_date=date(2026, 9, 25), project=self.project)
        Task.objects.create(title="Progress", status=Task.Status.IN_PROGRESS, due_date=date(2026, 9, 25), project=self.project)
        for index in range(3):
            Task.objects.create(title=f"Done {index}", status=Task.Status.DONE, due_date=date(2026, 9, 25), project=self.project)
        counts = {row["status"]: row["count"] for row in status_counts_for_project(self.project)}
        self.assertEqual(counts, {Task.Status.TODO: 2, Task.Status.IN_PROGRESS: 1, Task.Status.DONE: 3})


class TaskCreationTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.assignee = User.objects.create_user(username="ravi", password=self.password)
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)
        self.url = f"/projects/{self.project.pk}/tasks/create/"

    def test_anonymous_user_is_redirected_to_login(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")

    def test_owner_can_create_assigned_task_for_project(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(self.url, {"title": "Build homepage", "status": "TODO", "priority": "HIGH", "due_date": "2026-09-25", "assigned_to": self.assignee.pk})

        task = Task.objects.get(title="Build homepage")
        self.assertRedirects(response, f"/projects/{self.project.pk}/")
        self.assertEqual(task.project, self.project)
        self.assertEqual(task.assigned_to, self.assignee)

    def test_unassigned_task_is_allowed(self):
        self.client.login(username="aman", password=self.password)
        self.client.post(self.url, {"title": "Create schema", "status": "TODO", "priority": "MEDIUM", "due_date": "2026-09-25", "assigned_to": ""})
        self.assertIsNone(Task.objects.get(title="Create schema").assigned_to)

    def test_non_owner_cannot_create_task(self):
        self.client.login(username="ravi", password=self.password)
        response = self.client.post(self.url, {"title": "Unauthorized", "due_date": "2026-09-25"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Task.objects.filter(title="Unauthorized").exists())

    def test_project_is_not_a_form_field_and_posted_project_is_ignored(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'name="project"')
        self.client.post(self.url, {"title": "Safe task", "status": "TODO", "priority": "MEDIUM", "due_date": "2026-09-25", "project": "999"})
        self.assertEqual(Task.objects.get(title="Safe task").project, self.project)

    def test_invalid_choice_does_not_create_task(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(self.url, {"title": "Invalid", "status": "INVALID", "priority": "INVALID", "due_date": "2026-09-25"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title="Invalid").exists())


class TaskVisibilityTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.assignee = User.objects.create_user(username="ravi", password=self.password)
        self.unrelated = User.objects.create_user(username="raj", password=self.password)
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)
        self.task = Task.objects.create(
            title="Build homepage", due_date=date(2026, 9, 25), project=self.project, assigned_to=self.assignee
        )

    def test_assigned_member_can_view_all_project_tasks_and_task_detail(self):
        self.client.login(username="ravi", password=self.password)
        project_response = self.client.get(f"/projects/{self.project.pk}/")
        task_response = self.client.get(f"/projects/{self.project.pk}/tasks/{self.task.pk}/")
        self.assertEqual(project_response.status_code, 200)
        self.assertContains(project_response, "Build homepage")
        self.assertEqual(task_response.status_code, 200)

    def test_assignee_project_list_has_no_duplicate_projects(self):
        Task.objects.create(title="Second task", due_date=date(2026, 9, 26), project=self.project, assigned_to=self.assignee)
        self.client.login(username="ravi", password=self.password)

        response = self.client.get("/projects/")

        self.assertEqual(list(response.context["projects"]), [self.project])

    def test_reassignment_removes_membership_when_no_assignment_remains(self):
        self.task.assigned_to = self.owner
        self.task.save(update_fields=["assigned_to"])
        self.client.login(username="ravi", password=self.password)

        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/").status_code, 403)
        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/tasks/{self.task.pk}/").status_code, 403)

    def test_unassigned_task_does_not_create_membership(self):
        self.task.assigned_to = None
        self.task.save(update_fields=["assigned_to"])
        self.client.login(username="raj", password=self.password)

        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/").status_code, 403)

    def test_assigned_member_is_view_only_for_project_and_task_writes(self):
        self.client.login(username="ravi", password=self.password)
        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/edit/").status_code, 403)
        self.assertEqual(self.client.post(f"/projects/{self.project.pk}/delete/").status_code, 403)
        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/tasks/{self.task.pk}/edit/").status_code, 403)
        self.assertEqual(self.client.post(f"/projects/{self.project.pk}/tasks/{self.task.pk}/delete/").status_code, 403)

    def test_unrelated_user_cannot_view_project_or_task(self):
        self.client.login(username="raj", password=self.password)
        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/").status_code, 403)
        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/tasks/{self.task.pk}/").status_code, 403)

    def test_task_detail_requires_matching_project_id(self):
        other_project = Project.objects.create(name="Other Project", owner=self.owner)
        self.client.login(username="aman", password=self.password)
        self.assertEqual(self.client.get(f"/projects/{other_project.pk}/tasks/{self.task.pk}/").status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        self.assertRedirects(
            self.client.get(f"/projects/{self.project.pk}/tasks/{self.task.pk}/"),
            f"/login/?next=/projects/{self.project.pk}/tasks/{self.task.pk}/",
        )


class TaskEditPermissionTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.assignee = User.objects.create_user(username="ravi", password=self.password)
        self.other_user = User.objects.create_user(username="raj", password=self.password)
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)
        self.other_project = Project.objects.create(name="Other Project", owner=self.owner)
        self.task = Task.objects.create(
            title="Build homepage", status=Task.Status.TODO, priority=Task.Priority.HIGH,
            due_date=date(2026, 9, 25), project=self.project, assigned_to=self.assignee,
        )
        self.url = f"/projects/{self.project.pk}/tasks/{self.task.pk}/edit/"

    def test_anonymous_user_is_redirected_to_login(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")

    def test_owner_can_edit_task_without_changing_project(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(self.url, {"title": "Build homepage v2", "status": "DONE", "priority": "LOW", "due_date": "2026-10-01", "assigned_to": self.other_user.pk, "project": self.other_project.pk})
        self.assertRedirects(response, f"/projects/{self.project.pk}/tasks/{self.task.pk}/")
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Build homepage v2")
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertEqual(self.task.assigned_to, self.other_user)
        self.assertEqual(self.task.project, self.project)

    def test_assignee_and_unrelated_user_cannot_edit(self):
        for username in ("ravi", "raj"):
            self.client.login(username=username, password=self.password)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            response = self.client.post(self.url, {"title": "Hacked", "status": "DONE", "priority": "HIGH", "due_date": "2026-10-01"})
            self.assertEqual(response.status_code, 403)
            self.client.logout()
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Build homepage")

    def test_mismatched_project_url_returns_not_found(self):
        self.client.login(username="aman", password=self.password)
        self.assertEqual(self.client.get(f"/projects/{self.other_project.pk}/tasks/{self.task.pk}/edit/").status_code, 404)

    def test_invalid_choices_do_not_update_task(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(self.url, {"title": "Changed", "status": "BAD", "priority": "BAD", "due_date": "2026-10-01"})
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Build homepage")


class TaskDeletePermissionTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.assignee = User.objects.create_user(username="ravi", password=self.password)
        self.other_user = User.objects.create_user(username="raj", password=self.password)
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)
        self.other_project = Project.objects.create(name="Other Project", owner=self.owner)
        self.task = Task.objects.create(title="Build homepage", due_date=date(2026, 9, 25), project=self.project, assigned_to=self.assignee)
        self.url = f"/projects/{self.project.pk}/tasks/{self.task.pk}/delete/"

    def test_anonymous_user_is_redirected_to_login(self):
        self.assertRedirects(self.client.get(self.url), f"/login/?next={self.url}")

    def test_owner_can_view_confirmation_without_deleting(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This action cannot be undone.")
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_owner_can_delete_task_with_post(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(self.url)
        self.assertRedirects(response, f"/projects/{self.project.pk}/")
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_assignee_and_unrelated_user_cannot_delete(self):
        for username in ("ravi", "raj"):
            self.client.login(username=username, password=self.password)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.client.post(self.url).status_code, 403)
            self.client.logout()
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_mismatched_project_url_returns_not_found(self):
        self.client.login(username="aman", password=self.password)
        self.assertEqual(self.client.get(f"/projects/{self.other_project.pk}/tasks/{self.task.pk}/delete/").status_code, 404)

# Create your tests here.
