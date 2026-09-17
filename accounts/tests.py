from django.contrib.auth import get_user_model
from datetime import date

from django.test import TestCase

from projects.models import Project
from tasks.models import Task


User = get_user_model()


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"

    def create_user(self, username="aman"):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=self.password,
        )

    def test_user_can_register_with_valid_data(self):
        response = self.client.post(
            "/register/",
            {
                "username": "aman",
                "email": "aman@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertRedirects(response, "/login/")
        user = User.objects.get(username="aman")
        self.assertEqual(user.email, "aman@example.com")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))

    def test_duplicate_username_is_rejected(self):
        self.create_user()

        response = self.client.post(
            "/register/",
            {
                "username": "aman",
                "email": "other@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="aman").count(), 1)

    def test_password_mismatch_does_not_create_user(self):
        response = self.client.post(
            "/register/",
            {
                "username": "aman",
                "email": "aman@example.com",
                "password1": self.password,
                "password2": "DifferentPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="aman").exists())

    def test_invalid_email_does_not_create_user(self):
        response = self.client.post(
            "/register/",
            {
                "username": "aman",
                "email": "not-an-email",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="aman").exists())

    def test_user_can_login_with_valid_credentials(self):
        self.create_user()

        response = self.client.post("/login/", {"username": "aman", "password": self.password})

        self.assertRedirects(response, "/dashboard/")
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(self.client.get("/dashboard/").status_code, 200)

    def test_invalid_credentials_do_not_authenticate_user(self):
        self.create_user()

        response = self.client.post("/login/", {"username": "aman", "password": "WrongPassword123!"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/dashboard/")

        self.assertRedirects(response, "/login/?next=/dashboard/")

    def test_authenticated_user_can_access_dashboard(self):
        self.create_user()
        self.client.login(username="aman", password=self.password)

        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back, aman")

    def test_logout_ends_session_but_keeps_user(self):
        user = self.create_user()
        self.client.login(username="aman", password=self.password)

        response = self.client.post("/logout/")

        self.assertRedirects(response, "/login/")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.get("/dashboard/"), "/login/?next=/dashboard/")
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_get_logout_is_not_allowed(self):
        self.assertEqual(self.client.get("/logout/").status_code, 405)

    def test_dashboard_contains_only_tasks_assigned_to_current_user(self):
        owner = User.objects.create_user(username="owner", password=self.password)
        other = User.objects.create_user(username="other", password=self.password)
        project = Project.objects.create(name="Dashboard Project", owner=owner)
        assigned = Task.objects.create(title="Assigned task", due_date="2026-09-20", project=project, assigned_to=owner)
        Task.objects.create(title="Other task", due_date="2026-09-19", project=project, assigned_to=other)
        Task.objects.create(title="Unassigned task", due_date="2026-09-18", project=project)
        self.client.login(username="owner", password=self.password)

        response = self.client.get("/dashboard/")

        self.assertEqual(list(response.context["tasks"]), [assigned])

    def test_dashboard_is_protected(self):
        response = self.client.get("/dashboard/")
        self.assertRedirects(response, "/login/?next=/dashboard/")

    def test_dashboard_groups_assigned_tasks_and_excludes_other_users(self):
        user = User.objects.create_user(username="ravi", password=self.password)
        other = User.objects.create_user(username="neha", password=self.password)
        project = Project.objects.create(name="Dashboard Project", owner=other)
        todo = Task.objects.create(title="Todo task", status=Task.Status.TODO, due_date=date(2026, 9, 20), project=project, assigned_to=user)
        progress = Task.objects.create(title="Progress task", status=Task.Status.IN_PROGRESS, due_date=date(2026, 9, 21), project=project, assigned_to=user)
        done = Task.objects.create(title="Done task", status=Task.Status.DONE, due_date=date(2026, 9, 10), project=project, assigned_to=user)
        overdue = Task.objects.create(title="Overdue task", status=Task.Status.TODO, due_date=date(2026, 9, 15), project=project, assigned_to=user)
        Task.objects.create(title="Other user's task", project=project, assigned_to=other, due_date=date(2026, 9, 14))
        Task.objects.create(title="Unassigned task", project=project, due_date=date(2026, 9, 13))
        self.client.login(username="ravi", password=self.password)

        response = self.client.get("/dashboard/")

        self.assertEqual(response.context["todo_tasks"], [overdue, todo])
        self.assertEqual(response.context["in_progress_tasks"], [progress])
        self.assertEqual(response.context["done_tasks"], [done])
        self.assertEqual(response.context["overdue_tasks"], [overdue])
        self.assertNotContains(response, "Other user's task")
        self.assertNotContains(response, "Unassigned task")

    def test_dashboard_has_all_three_empty_status_sections(self):
        user = User.objects.create_user(username="ravi", password=self.password)
        self.client.login(username="ravi", password=self.password)

        response = self.client.get("/dashboard/")

        self.assertContains(response, "No To Do tasks.")
        self.assertContains(response, "No In Progress tasks.")
        self.assertContains(response, "No completed tasks.")
        self.assertContains(response, "No tasks assigned to you yet.")

# Create your tests here.
