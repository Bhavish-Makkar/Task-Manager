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

# Create your tests here.
