from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from projects.models import Project
from tasks.models import Task

from .models import Comment


class CommentModelTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="aman", password="StrongPassword123!")
        self.project = Project.objects.create(name="Website Redesign", owner=self.author)
        self.task = Task.objects.create(title="Build homepage", due_date="2026-09-25", project=self.project)

    def test_comment_has_task_author_body_and_automatic_timestamp(self):
        before = timezone.now()
        comment = Comment.objects.create(task=self.task, author=self.author, body="Please update the CTA copy.")
        after = timezone.now()

        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.author, self.author)
        self.assertEqual(comment.body, "Please update the CTA copy.")
        self.assertTrue(before <= comment.timestamp <= after)

    def test_task_can_have_multiple_comments_in_oldest_first_order(self):
        first = Comment.objects.create(task=self.task, author=self.author, body="First")
        second = Comment.objects.create(task=self.task, author=self.author, body="Second")

        self.assertEqual(list(self.task.comments.all()), [first, second])

    def test_task_deletion_cascades_to_comments(self):
        comment = Comment.objects.create(task=self.task, author=self.author, body="Remove with task")
        self.task.delete()

        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_empty_body_is_rejected_by_model_validation(self):
        comment = Comment(task=self.task, author=self.author, body="")

        with self.assertRaisesMessage(ValidationError, "This field cannot be blank"):
            comment.full_clean()


class CommentCreationTests(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.owner = User.objects.create_user(username="aman", password=self.password)
        self.member = User.objects.create_user(username="ravi", password=self.password)
        self.unrelated = User.objects.create_user(username="raj", password=self.password)
        self.project = Project.objects.create(name="Website Redesign", owner=self.owner)
        self.task = Task.objects.create(title="Build homepage", due_date="2026-09-25", project=self.project, assigned_to=self.member)
        self.url = f"/projects/{self.project.pk}/tasks/{self.task.pk}/comments/create/"

    def test_owner_can_add_comment_with_server_bound_author_and_task(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(self.url, {"body": "Please review this." , "author": self.member.pk, "task": 999})
        comment = Comment.objects.get()
        self.assertRedirects(response, f"/projects/{self.project.pk}/tasks/{self.task.pk}/")
        self.assertEqual(comment.author, self.owner)
        self.assertEqual(comment.task, self.task)
        self.assertIsNotNone(comment.timestamp)

    def test_assigned_member_can_add_comment(self):
        self.client.login(username="ravi", password=self.password)
        response = self.client.post(self.url, {"body": "I will check this."})
        self.assertRedirects(response, f"/projects/{self.project.pk}/tasks/{self.task.pk}/")
        self.assertEqual(Comment.objects.get().author, self.member)

    def test_unrelated_user_cannot_add_comment(self):
        self.client.login(username="raj", password=self.password)
        self.assertEqual(self.client.post(self.url, {"body": "Not allowed."}).status_code, 403)
        self.assertFalse(Comment.objects.exists())

    def test_anonymous_user_is_redirected_to_login(self):
        self.assertRedirects(self.client.post(self.url, {"body": "Sign in first."}), f"/login/?next={self.url}")

    def test_empty_comment_is_rejected_without_creating_comment(self):
        self.client.login(username="aman", password=self.password)
        response = self.client.post(self.url, {"body": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.exists())

    def test_mismatched_project_task_url_returns_not_found(self):
        other_project = Project.objects.create(name="Other", owner=self.owner)
        self.client.login(username="aman", password=self.password)
        self.assertEqual(self.client.post(f"/projects/{other_project.pk}/tasks/{self.task.pk}/comments/create/", {"body": "Wrong task."}).status_code, 404)

    def test_task_detail_renders_comments_oldest_first_without_author_n_plus_one(self):
        first = Comment.objects.create(task=self.task, author=self.author, body="First comment")
        second = Comment.objects.create(task=self.task, author=self.author, body="Second comment")
        self.client.login(username="aman", password=self.password)

        with self.assertNumQueries(3):
            response = self.client.get(f"/projects/{self.project.pk}/tasks/{self.task.pk}/")

        self.assertContains(response, "First comment")
        self.assertContains(response, "Second comment")
        content = response.content.decode()
        self.assertLess(content.index("First comment"), content.index("Second comment"))

    def test_task_detail_shows_empty_comment_state(self):
        self.client.login(username="aman", password=self.password)

        response = self.client.get(f"/projects/{self.project.pk}/tasks/{self.task.pk}/")

        self.assertContains(response, "No comments yet. Be the first to add one.")

# Create your tests here.
