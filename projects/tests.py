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

    def test_project_form_does_not_expose_owner_field(self):
        self.client.login(username="aman", password=self.password)

        response = self.client.get("/projects/create/")

        self.assertNotContains(response, 'name="owner"')
        self.assertNotContains(response, 'name="owner_id"')


class ProjectListAndDetailTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.other_user = User.objects.create_user(username="ravi", password=self.password)
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)

    def test_anonymous_user_cannot_view_list_or_detail(self):
        self.assertRedirects(self.client.get("/projects/"), "/login/?next=/projects/")
        self.assertRedirects(
            self.client.get(f"/projects/{self.project.pk}/"),
            f"/login/?next=/projects/{self.project.pk}/",
        )

    def test_owner_sees_owned_projects_in_list(self):
        self.client.login(username="aman", password=self.password)

        response = self.client.get("/projects/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Website Redesign")

    def test_owner_can_view_project_detail(self):
        self.client.login(username="aman", password=self.password)

        response = self.client.get(f"/projects/{self.project.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit project")

    def test_non_owner_cannot_view_project_or_see_it_in_list(self):
        self.client.login(username="ravi", password=self.password)

        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/").status_code, 404)
        self.assertNotContains(self.client.get("/projects/"), "Website Redesign")

    def test_empty_project_list_has_empty_state(self):
        self.client.login(username="ravi", password=self.password)

        response = self.client.get("/projects/")

        self.assertContains(response, "No projects yet")


class ProjectEditPermissionTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.other_user = User.objects.create_user(username="ravi", password=self.password)
        self.project = Project.objects.create(
            name="Website Redesign", description="Old description", owner=self.owner
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(f"/projects/{self.project.pk}/edit/")
        self.assertRedirects(response, f"/login/?next=/projects/{self.project.pk}/edit/")

    def test_owner_can_open_edit_page(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.get(f"/projects/{self.project.pk}/edit/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit project")
        self.assertNotContains(response, "owner")

    def test_owner_can_update_name_and_description(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(
            f"/projects/{self.project.pk}/edit/",
            {"name": "Website Revamp", "description": "New description", "owner_id": self.other_user.pk},
        )
        self.assertRedirects(response, f"/projects/{self.project.pk}/")
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Website Revamp")
        self.assertEqual(self.project.description, "New description")
        self.assertEqual(self.project.owner, self.owner)

    def test_non_owner_get_is_forbidden(self):
        self.client.login(username="ravi", password=self.password)
        self.assertEqual(self.client.get(f"/projects/{self.project.pk}/edit/").status_code, 403)

    def test_non_owner_post_is_forbidden_and_data_unchanged(self):
        self.client.login(username="ravi", password=self.password)
        response = self.client.post(
            f"/projects/{self.project.pk}/edit/",
            {"name": "Hacked", "description": "Tampered", "owner_id": self.other_user.pk},
        )
        self.assertEqual(response.status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Website Redesign")
        self.assertEqual(self.project.description, "Old description")
        self.assertEqual(self.project.owner, self.owner)


class ProjectDeletePermissionTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.other_user = User.objects.create_user(username="ravi", password=self.password)
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(f"/projects/{self.project.pk}/delete/")
        self.assertRedirects(response, f"/login/?next=/projects/{self.project.pk}/delete/")

    def test_owner_can_view_delete_confirmation(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.get(f"/projects/{self.project.pk}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This action cannot be undone.")

    def test_owner_can_delete_project_with_post(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(f"/projects/{self.project.pk}/delete/")
        self.assertRedirects(response, "/projects/")
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.owner.pk).exists())

    def test_non_owner_get_and_post_are_forbidden(self):
        self.client.login(username="ravi", password=self.password)
        url = f"/projects/{self.project.pk}/delete/"

        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_get_does_not_delete_project(self):
        self.client.login(username="aman", password=self.password)
        self.client.get(f"/projects/{self.project.pk}/delete/")
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

# Create your tests here.
