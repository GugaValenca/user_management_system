from unittest import mock

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserActivityLog
from .views import LoginRateThrottle


def create_user(**overrides):
    defaults = {
        "email": "test.user@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPass123!",
    }
    defaults.update(overrides)
    return User.objects.create_user(**defaults)


class AuthLoginTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.user = create_user(
            email="admin.test@example.com",
            username="admintest",
            first_name="Admin",
            last_name="Test",
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

    def test_login_disabled_account_is_rejected(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            self.login_url,
            {"identifier": self.user.username, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthRegisterTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")

    def test_register_creates_user_and_returns_tokens(self):
        response = self.client.post(
            self.register_url,
            {
                "email": "new.user@example.com",
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new.user@example.com").exists())
        self.assertEqual(response.data["user"]["role"], "user")
        self.assertTrue(
            UserActivityLog.objects.filter(
                user__email="new.user@example.com", activity_type="register"
            ).exists()
        )

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            self.register_url,
            {
                "email": "mismatch@example.com",
                "username": "mismatch",
                "first_name": "Mis",
                "last_name": "Match",
                "password": "TestPass123!",
                "password_confirm": "Different123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="mismatch@example.com").exists())

    def test_register_ignores_client_supplied_role(self):
        response = self.client.post(
            self.register_url,
            {
                "email": "escalation@example.com",
                "username": "escalation",
                "first_name": "Esc",
                "last_name": "Alation",
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
                "role": "admin",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="escalation@example.com")
        self.assertEqual(user.role, "user")

    def test_register_rejects_duplicate_email(self):
        create_user(email="dup@example.com", username="dupuser")

        response = self.client.post(
            self.register_url,
            {
                "email": "dup@example.com",
                "username": "anotheruser",
                "first_name": "Dup",
                "last_name": "User",
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthLogoutTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.logout_url = reverse("logout")

    def _authenticate(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return str(refresh)

    def test_logout_blacklists_refresh_token(self):
        refresh_token = self._authenticate()

        response = self.client.post(
            self.logout_url, {"refresh_token": refresh_token}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="logout").exists()
        )

        # The same refresh token can no longer be used once blacklisted.
        second_response = self.client.post(
            self.logout_url, {"refresh_token": refresh_token}, format="json"
        )
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_requires_authentication(self):
        response = self.client.post(self.logout_url, {"refresh_token": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token_returns_400(self):
        self._authenticate()

        response = self.client.post(self.logout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.profile_url = reverse("profile")

    def test_get_profile_returns_current_user(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_update_profile_logs_activity(self):
        response = self.client.patch(self.profile_url, {"bio": "Backend developer"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "Backend developer")
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="profile_update").exists()
        )

    def test_update_profile_cannot_change_role(self):
        response = self.client.patch(self.profile_url, {"role": "admin"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "user")

    def test_profile_requires_authentication(self):
        self.client.credentials()
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordChangeTests(APITestCase):
    def setUp(self):
        self.password = "TestPass123!"
        self.user = create_user(password=self.password)
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.change_password_url = reverse("change_password")

    def test_change_password_succeeds_and_logs_activity(self):
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": self.password,
                "new_password": "NewPass456!",
                "new_password_confirm": "NewPass456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="password_change").exists()
        )

    def test_change_password_rejects_wrong_old_password(self):
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": "wrong-password",
                "new_password": "NewPass456!",
                "new_password_confirm": "NewPass456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))

    def test_change_password_rejects_mismatched_confirmation(self):
        response = self.client.post(
            self.change_password_url,
            {
                "old_password": self.password,
                "new_password": "NewPass456!",
                "new_password_confirm": "Different789!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ActivityLogTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="owner@example.com", username="owner")
        self.other_user = create_user(email="other@example.com", username="other")
        UserActivityLog.objects.create(
            user=self.user, activity_type="login", description="owner login"
        )
        UserActivityLog.objects.create(
            user=self.other_user, activity_type="login", description="other login"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.activity_url = reverse("activity_logs")

    def test_activity_logs_are_scoped_to_current_user(self):
        response = self.client.get(self.activity_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {entry["user_email"] for entry in response.data}
        self.assertEqual(emails, {self.user.email})


class AdminEndpointTests(APITestCase):
    def setUp(self):
        self.admin = create_user(email="admin@example.com", username="adminuser", role="admin")
        self.regular_user = create_user(email="regular@example.com", username="regularuser")
        self.users_url = reverse("user_list")
        self.stats_url = reverse("user_stats")

    def _authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_regular_user_cannot_list_users(self):
        self._authenticate_as(self.regular_user)

        response = self.client.get(self.users_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self._authenticate_as(self.admin)

        response = self.client.get(self.users_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_view_stats(self):
        self._authenticate_as(self.regular_user)

        response = self.client.get(self.stats_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_stats_reflect_user_counts(self):
        self._authenticate_as(self.admin)

        response = self.client.get(self.stats_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_users"], 2)
        self.assertEqual(response.data["admin_users"], 1)


class LoginThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.password = "TestPass123!"
        self.user = create_user(password=self.password)
        self.login_url = reverse("login")

    def tearDown(self):
        cache.clear()

    @mock.patch.dict(LoginRateThrottle.THROTTLE_RATES, {"login": "2/min"})
    def test_repeated_login_attempts_are_throttled(self):
        for _ in range(2):
            response = self.client.post(
                self.login_url,
                {"identifier": self.user.username, "password": "wrong-password"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        throttled_response = self.client.post(
            self.login_url,
            {"identifier": self.user.username, "password": self.password},
            format="json",
        )

        self.assertEqual(throttled_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AuthHealthEndpointTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="healthcheck@example.com", username="healthcheck")
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
