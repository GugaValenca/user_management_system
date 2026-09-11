import re
from unittest import mock

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserActivityLog
from .tokens import email_verification_token
from .views import LoginRateThrottle


def extract_link_params(email_body):
    """Pulls uid/token query params out of the link in a sent email body."""
    match = re.search(r"[?&]uid=([^&\s]+)&token=([^&\s]+)", email_body)
    assert match, f"No uid/token link found in email body:\n{email_body}"
    return match.group(1), match.group(2)


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
        cache.clear()
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
        self.assertTrue(response.data["is_active"])

    def test_profile_cannot_deactivate_self(self):
        response = self.client.patch(self.profile_url, {"is_active": False}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

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
        emails = {entry["user_email"] for entry in response.data["results"]}
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


class RegistrationEmailTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_register_sends_a_verification_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "verify.me@example.com",
                "username": "verifyme",
                "first_name": "Verify",
                "last_name": "Me",
                "password": "TestPass123!",
                "password_confirm": "TestPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify.me@example.com", mail.outbox[0].to)
        self.assertIn("verify-email", mail.outbox[0].body)


class EmailVerificationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = create_user(email="unverified@example.com", username="unverified")
        self.confirm_url = reverse("verify_email_confirm")

    def test_confirm_with_valid_token_marks_email_verified(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = email_verification_token.make_token(self.user)

        response = self.client.post(self.confirm_url, {"uid": uid, "token": token}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="email_verified").exists()
        )

    def test_confirm_with_invalid_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            self.confirm_url, {"uid": uid, "token": "not-a-real-token"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_password_reset_token_cannot_be_used_to_verify_email(self):
        """Tokens are salted per-purpose, so one can't be replayed as the other."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        password_reset_token = default_token_generator.make_token(self.user)

        response = self.client.post(
            self.confirm_url, {"uid": uid, "token": password_reset_token}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.resend_url = reverse("verify_email_resend")

    def _authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_resend_requires_authentication(self):
        response = self.client.post(self.resend_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_resend_sends_a_new_email_for_unverified_user(self):
        user = create_user(email="stillunverified@example.com", username="stillunverified")
        self._authenticate_as(user)

        response = self.client.post(self.resend_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_is_a_no_op_for_already_verified_user(self):
        user = create_user(
            email="alreadyverified@example.com",
            username="alreadyverified",
            is_email_verified=True,
        )
        self._authenticate_as(user)

        response = self.client.post(self.resend_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)


class PasswordResetTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.password = "TestPass123!"
        self.user = create_user(email="reset.me@example.com", password=self.password)
        self.request_url = reverse("password_reset_request")
        self.confirm_url = reverse("password_reset_confirm")

    def test_request_sends_email_for_existing_user(self):
        response = self.client.post(self.request_url, {"email": self.user.email}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    def test_request_returns_same_response_for_unknown_email(self):
        known_response = self.client.post(
            self.request_url, {"email": self.user.email}, format="json"
        )
        mail.outbox.clear()
        unknown_response = self.client.post(
            self.request_url, {"email": "nobody@example.com"}, format="json"
        )

        self.assertEqual(known_response.status_code, unknown_response.status_code)
        self.assertEqual(known_response.data, unknown_response.data)
        # ... but only the real account actually receives an email.
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_with_valid_token_changes_password(self):
        self.client.post(self.request_url, {"email": self.user.email}, format="json")
        uid, token = extract_link_params(mail.outbox[0].body)

        response = self.client.post(
            self.confirm_url,
            {
                "uid": uid,
                "token": token,
                "new_password": "BrandNewPass456!",
                "new_password_confirm": "BrandNewPass456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass456!"))
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="password_reset").exists()
        )

    def test_confirm_invalidates_existing_refresh_tokens(self):
        refresh = RefreshToken.for_user(self.user)
        OutstandingToken.objects.get_or_create(
            user=self.user,
            jti=refresh["jti"],
            defaults={
                "token": str(refresh),
                "created_at": refresh.current_time,
                "expires_at": refresh.current_time,
            },
        )

        self.client.post(self.request_url, {"email": self.user.email}, format="json")
        uid, token = extract_link_params(mail.outbox[0].body)
        self.client.post(
            self.confirm_url,
            {
                "uid": uid,
                "token": token,
                "new_password": "BrandNewPass456!",
                "new_password_confirm": "BrandNewPass456!",
            },
            format="json",
        )

        self.assertTrue(BlacklistedToken.objects.filter(token__user=self.user).exists())

    def test_confirm_rejects_mismatched_passwords(self):
        self.client.post(self.request_url, {"email": self.user.email}, format="json")
        uid, token = extract_link_params(mail.outbox[0].body)

        response = self.client.post(
            self.confirm_url,
            {
                "uid": uid,
                "token": token,
                "new_password": "BrandNewPass456!",
                "new_password_confirm": "Different789!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_rejects_tampered_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            self.confirm_url,
            {
                "uid": uid,
                "token": "clearly-not-valid",
                "new_password": "BrandNewPass456!",
                "new_password_confirm": "BrandNewPass456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.password))


class TokenRefreshTests(APITestCase):
    def test_refresh_returns_a_new_access_token(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)

        response = self.client.post(
            reverse("token_refresh"), {"refresh": str(refresh)}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_rejects_an_invalid_token(self):
        response = self.client.post(
            reverse("token_refresh"), {"refresh": "not-a-real-token"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminUserDetailTests(APITestCase):
    def setUp(self):
        self.admin = create_user(email="admin2@example.com", username="admin2", role="admin")
        self.other_admin = create_user(email="admin3@example.com", username="admin3", role="admin")
        self.regular_user = create_user(email="target@example.com", username="target")

    def _authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_admin_can_promote_a_user(self):
        self._authenticate_as(self.admin)

        response = self.client.patch(
            reverse("admin_user_detail", args=[self.regular_user.pk]),
            {"role": "moderator"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.role, "moderator")
        self.assertTrue(
            UserActivityLog.objects.filter(
                user=self.regular_user, activity_type="admin_update"
            ).exists()
        )

    def test_admin_can_deactivate_a_user(self):
        self._authenticate_as(self.admin)

        response = self.client.patch(
            reverse("admin_user_detail", args=[self.regular_user.pk]),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

    def test_admin_cannot_change_their_own_account_here(self):
        self._authenticate_as(self.admin)

        response = self.client.patch(
            reverse("admin_user_detail", args=[self.admin.pk]),
            {"role": "user"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, "admin")

    def test_admin_can_still_change_another_admin(self):
        self._authenticate_as(self.admin)

        response = self.client.patch(
            reverse("admin_user_detail", args=[self.other_admin.pk]),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_update_users(self):
        self._authenticate_as(self.regular_user)

        response = self.client.patch(
            reverse("admin_user_detail", args=[self.other_admin.pk]),
            {"role": "user"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_cannot_touch_fields_outside_the_admin_serializer(self):
        self._authenticate_as(self.admin)

        response = self.client.patch(
            reverse("admin_user_detail", args=[self.regular_user.pk]),
            {"email": "hijacked@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.email, "target@example.com")


class AdminUserSearchTests(APITestCase):
    def setUp(self):
        self.admin = create_user(
            email="search.admin@example.com", username="searchadmin", role="admin"
        )
        create_user(email="alice@example.com", username="alice", role="moderator")
        create_user(email="bob@example.com", username="bob", role="user")
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.users_url = reverse("user_list")

    def test_search_filters_by_email_or_username(self):
        response = self.client.get(self.users_url, {"search": "alice"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {u["email"] for u in response.data["results"]}
        self.assertEqual(emails, {"alice@example.com"})

    def test_filter_by_role(self):
        response = self.client.get(self.users_url, {"role": "moderator"})

        roles = {u["role"] for u in response.data["results"]}
        self.assertEqual(roles, {"moderator"})

    def test_filter_by_active_status(self):
        inactive_user = create_user(email="inactive@example.com", username="inactive")
        inactive_user.is_active = False
        inactive_user.save(update_fields=["is_active"])

        response = self.client.get(self.users_url, {"is_active": "false"})

        emails = {u["email"] for u in response.data["results"]}
        self.assertEqual(emails, {"inactive@example.com"})
