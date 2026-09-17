from django.contrib.auth.models import User
from django.test import TestCase

from .models import Project


class ProjectModelTests(TestCase):
    def test_project_has_required_owner_and_core_fields(self):
        owner = User.objects.create_user(username="aman", password="StrongPassword123!")
        project = Project.objects.create(
            name="Website Redesign",
            description="Update the company website.",
            owner=owner,
        )

        self.assertEqual(project.owner, owner)
        self.assertEqual(owner.projects.count(), 1)
        self.assertEqual(str(project), "Website Redesign")

    def test_one_user_can_own_multiple_projects(self):
        owner = User.objects.create_user(username="aman", password="StrongPassword123!")
        Project.objects.create(name="Project One", owner=owner)
        Project.objects.create(name="Project Two", owner=owner)

        self.assertEqual(Project.objects.filter(owner=owner).count(), 2)


class ProjectCreationTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get("/projects/create/")

        self.assertRedirects(response, "/login/?next=/projects/create/")

    def test_authenticated_user_can_create_project_with_themselves_as_owner(self):
        self.client.login(username="aman", password=self.password)

        response = self.client.post(
            "/projects/create/",
            {"name": "Website Redesign", "description": "Update the company website."},
        )

        project = Project.objects.get(name="Website Redesign")
        self.assertRedirects(response, f"/projects/{project.pk}/")
        self.assertEqual(project.owner, self.owner)

    def test_owner_is_not_taken_from_post_data(self):
        self.client.login(username="aman", password=self.password)

        self.client.post(
            "/projects/create/",
            {"name": "Safe Project", "description": "", "owner": "999", "owner_id": "999"},
        )

        self.assertEqual(Project.objects.get(name="Safe Project").owner, self.owner)

    def test_invalid_project_does_not_get_created(self):
        self.client.login(username="aman", password=self.password)

        response = self.client.post("/projects/create/", {"name": "", "description": "Details"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(description="Details").exists())

# Create your tests here.
