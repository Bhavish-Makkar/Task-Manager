from django.contrib.auth import get_user_model
from django.test import TestCase


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

# Create your tests here.
