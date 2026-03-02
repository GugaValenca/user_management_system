from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, UserActivityLog


class AuthLoginTests(APITestCase):
    def setUp(self):
        self.password = "@Tampa5000"
        self.user = User.objects.create_user(
            email="gustavo_valenca@hotmail.com",
            username="GugaTampa",
            first_name="Gustavo",
            last_name="Valenca",
            password=self.password,
            role="admin",
        )
        self.login_url = reverse("login")

    def test_login_with_username_returns_tokens_and_logs_activity(self):
        response = self.client.post(
            self.login_url,
            {"identifier": self.user.username, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["user"]["username"], self.user.username)
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="login").exists()
        )

    def test_login_with_email_returns_tokens(self):
        response = self.client.post(
            self.login_url,
            {"identifier": self.user.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], self.user.email)

    def test_login_invalid_credentials_returns_400(self):
        response = self.client.post(
            self.login_url,
            {"identifier": self.user.username, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthHealthEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="healthcheck@example.com",
            username="healthcheck",
            first_name="Health",
            last_name="Check",
            password="ComplexPass123!",
        )
        UserActivityLog.objects.create(
            user=self.user,
            activity_type="login",
            description="User logged in successfully",
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

    def test_auth_health_endpoint_returns_login_metrics(self):
        response = self.client.get("/health/auth/")
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload["status"], "ok")
        self.assertIn("auth", payload)
        self.assertGreaterEqual(payload["auth"]["successful_logins_last_24h"], 1)
        self.assertIsNotNone(payload["auth"]["last_successful_login_utc"])
