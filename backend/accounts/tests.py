import io
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .cookies import REFRESH_COOKIE_NAME, csrf_token_for_jti, extract_jti_unverified
from .models import User, UserActivityLog
from .tokens import email_verification_token
from .views import LoginRateThrottle


def extract_link_params(email_body):
    """Pulls uid/token query params out of the link in a sent email body."""
    match = re.search(r"[?&]uid=([^&\s]+)&token=([^&\s]+)", email_body)
    assert match, f"No uid/token link found in email body:\n{email_body}"
    return match.group(1), match.group(2)


def _generate_test_image(dimensions):
    """Random noise so PNG compression can't shrink a "large" image back
    under the size limit being tested against."""
    width, height = dimensions
    pixels = os.urandom(width * height * 3)
    image = Image.frombytes("RGB", (width, height), pixels)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile("test.png", buffer.read(), content_type="image/png")


def set_refresh_cookie(client, refresh_token):
    """Puts a refresh token on a test client's cookie jar and returns the
    X-Refresh-Csrf-Token header that actually matches it - mirroring what a
    real login/refresh response gives the frontend to work with (see
    accounts/cookies.py)."""
    client.cookies[REFRESH_COOKIE_NAME] = refresh_token
    jti = extract_jti_unverified(refresh_token)
    csrf_token = csrf_token_for_jti(jti) if jti else "unusable-csrf-token"
    return {"HTTP_X_REFRESH_CSRF_TOKEN": csrf_token}


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
        # The refresh token never appears in the body - it's set as an
        # httpOnly cookie instead (asserted in RefreshCookieTests).
        self.assertNotIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["user"]["username"], self.user.username)
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="login").exists()
        )

    def test_login_sets_an_httponly_refresh_cookie(self):
        response = self.client.post(
            self.login_url,
            {"identifier": self.user.username, "password": self.password},
            format="json",
        )

        refresh_cookie = response.cookies[REFRESH_COOKIE_NAME]
        self.assertTrue(refresh_cookie.value)
        self.assertTrue(refresh_cookie["httponly"])
        self.assertEqual(refresh_cookie["path"], "/api/auth/")

        # The CSRF token pairs with the cookie above via its jti - it has
        # to come back in the body since the cookie is httpOnly and (being
        # on a different origin from the frontend) unreadable by its JS
        # even if it weren't.
        jti = extract_jti_unverified(refresh_cookie.value)
        self.assertEqual(response.data["tokens"]["csrf_token"], csrf_token_for_jti(jti))

    def test_login_with_email_returns_tokens(self):
        response = self.client.post(
            self.login_url,
            {"identifier": self.user.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], self.user.email)

    def test_logged_ip_uses_the_last_forwarded_for_entry(self):
        """A client can set their own X-Forwarded-For header. A trusted
        proxy (Vercel) appends what it actually saw to the end of that
        header rather than replacing it, so trusting the first entry would
        let anyone forge whatever IP lands in the audit trail."""
        self.client.post(
            self.login_url,
            {"identifier": self.user.username, "password": self.password},
            format="json",
            HTTP_X_FORWARDED_FOR="203.0.113.9, 10.0.0.1",
        )

        log = UserActivityLog.objects.get(user=self.user, activity_type="login")
        self.assertEqual(log.ip_address, "10.0.0.1")

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
        self.assertNotIn("refresh", response.data["tokens"])
        self.assertTrue(response.cookies[REFRESH_COOKIE_NAME]["httponly"])
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
        csrf_headers = set_refresh_cookie(self.client, str(refresh))
        return str(refresh), csrf_headers

    def test_logout_blacklists_refresh_token(self):
        refresh_token, csrf_headers = self._authenticate()

        response = self.client.post(self.logout_url, **csrf_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            UserActivityLog.objects.filter(user=self.user, activity_type="logout").exists()
        )

        # The same refresh token can no longer be used once blacklisted -
        # re-set the cookie since the successful logout above cleared it.
        set_refresh_cookie(self.client, refresh_token)
        second_response = self.client.post(self.logout_url, **csrf_headers)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_clears_the_refresh_cookie(self):
        _, csrf_headers = self._authenticate()

        response = self.client.post(self.logout_url, **csrf_headers)

        self.assertEqual(response.cookies[REFRESH_COOKIE_NAME].value, "")

    def test_logout_requires_authentication(self):
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_cookie_returns_400(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = self.client.post(self.logout_url, HTTP_X_REFRESH_CSRF_TOKEN="some-csrf-token")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_rejects_a_mismatched_csrf_header(self):
        self._authenticate()

        response = self.client.post(self.logout_url, HTTP_X_REFRESH_CSRF_TOKEN="wrong-value")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_rejects_a_missing_csrf_header(self):
        self._authenticate()

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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

    def test_profile_picture_over_size_limit_is_rejected(self):
        oversized_image = _generate_test_image(dimensions=(2000, 1000))

        response = self.client.patch(
            self.profile_url, {"profile_picture": oversized_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_picture", response.data)

    def test_profile_picture_within_size_limit_is_accepted(self):
        small_image = _generate_test_image(dimensions=(20, 20))

        response = self.client.patch(
            self.profile_url, {"profile_picture": small_image}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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


class AdminActivityLogTests(APITestCase):
    def setUp(self):
        self.admin = create_user(email="logadmin@example.com", username="logadmin", role="admin")
        self.alice = create_user(email="alice@example.com", username="alice")
        self.bob = create_user(email="bob@example.com", username="bob")
        UserActivityLog.objects.create(
            user=self.alice, activity_type="login", description="alice login"
        )
        UserActivityLog.objects.create(
            user=self.bob, activity_type="password_change", description="bob changed password"
        )
        self.url = reverse("admin_activity_logs")

    def _authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_regular_user_cannot_view_system_wide_logs(self):
        self._authenticate_as(self.alice)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_sees_activity_from_every_user(self):
        self._authenticate_as(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = {entry["user_email"] for entry in response.data["results"]}
        self.assertEqual(emails, {self.alice.email, self.bob.email})
        usernames = {entry["username"] for entry in response.data["results"]}
        self.assertEqual(usernames, {"alice", "bob"})

    def test_search_filters_by_acting_user(self):
        self._authenticate_as(self.admin)

        response = self.client.get(self.url, {"search": "alice"})

        entries = response.data["results"]
        self.assertTrue(entries)
        self.assertTrue(all(entry["user_email"] == self.alice.email for entry in entries))

    def test_filter_by_activity_type(self):
        self._authenticate_as(self.admin)

        response = self.client.get(self.url, {"activity_type": "password_change"})

        entries = response.data["results"]
        self.assertTrue(entries)
        self.assertTrue(all(entry["activity_type"] == "password_change" for entry in entries))


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


class AdminLoginRateLimitMiddlewareTests(APITestCase):
    """Django's own admin login view has no throttling of its own - unlike
    every login path in the custom API. accounts.middleware closes that gap;
    these tests exercise the middleware directly against /admin/login/."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @mock.patch("accounts.middleware.ADMIN_LOGIN_MAX_ATTEMPTS", 3)
    def test_repeated_admin_login_attempts_are_throttled(self):
        for _ in range(3):
            response = self.client.post(
                "/admin/login/", {"username": "nobody", "password": "wrong"}
            )
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        throttled_response = self.client.post(
            "/admin/login/", {"username": "nobody", "password": "wrong"}
        )

        self.assertEqual(throttled_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_throttle_is_scoped_to_the_admin_login_path(self):
        for _ in range(15):
            response = self.client.get("/admin/")
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_throttle_counts_are_isolated_per_ip(self):
        with mock.patch("accounts.middleware.ADMIN_LOGIN_MAX_ATTEMPTS", 1):
            first = self.client.post(
                "/admin/login/",
                {"username": "nobody", "password": "wrong"},
                REMOTE_ADDR="10.0.0.1",
            )
            second = self.client.post(
                "/admin/login/",
                {"username": "nobody", "password": "wrong"},
                REMOTE_ADDR="10.0.0.2",
            )

        self.assertNotEqual(first.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertNotEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


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

        # The response-timing floor (a deliberate mitigation, see
        # views.request_password_reset) would otherwise add real delay to
        # every test in this class; it gets its own dedicated test below.
        floor_patcher = mock.patch("accounts.views.PASSWORD_RESET_RESPONSE_FLOOR_SECONDS", 0)
        floor_patcher.start()
        self.addCleanup(floor_patcher.stop)

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


class PasswordResetTimingTests(APITestCase):
    """The response-timing floor exists specifically so this endpoint can't
    be used to enumerate accounts by how fast it responds - see the comment
    in views.request_password_reset. These run with the real floor."""

    def setUp(self):
        cache.clear()
        self.request_url = reverse("password_reset_request")

    def test_unknown_email_still_takes_roughly_as_long_as_a_real_one(self):
        from accounts.views import PASSWORD_RESET_RESPONSE_FLOOR_SECONDS

        started_at = time.monotonic()
        response = self.client.post(
            self.request_url, {"email": "nobody-at-all@example.com"}, format="json"
        )
        elapsed = time.monotonic() - started_at

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(elapsed, PASSWORD_RESET_RESPONSE_FLOOR_SECONDS)


class LoginTimingTests(APITestCase):
    """Verifies the dummy password hash still runs for a nonexistent
    identifier - the actual defense is the resulting timing consistency,
    which isn't reliably assertable in a unit test, so this locks in the
    mechanism (make_password gets called either way) instead."""

    @mock.patch("accounts.serializers.make_password")
    def test_dummy_hash_runs_for_nonexistent_identifier(self, mocked_make_password):
        response = self.client.post(
            reverse("login"),
            {"identifier": "nobody-at-all@example.com", "password": "whatever123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mocked_make_password.assert_called_once_with("whatever123")

    @mock.patch("accounts.serializers.make_password")
    def test_dummy_hash_does_not_run_for_a_real_identifier(self, mocked_make_password):
        user = create_user()

        self.client.post(
            reverse("login"),
            {"identifier": user.username, "password": "wrong-password"},
            format="json",
        )

        mocked_make_password.assert_not_called()


class TokenRefreshTests(APITestCase):
    """The refresh endpoint now reads the token from its httpOnly cookie
    (see accounts/cookies.py) instead of the request body, and requires a
    CSRF header derived from that same token."""

    def _post_refresh(self, refresh_token):
        headers = set_refresh_cookie(self.client, refresh_token)
        return self.client.post(reverse("token_refresh"), **headers)

    def test_refresh_returns_a_new_access_token(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)

        response = self._post_refresh(str(refresh))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("csrf_token", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_rotates_the_cookie_and_blacklists_the_old_token(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)

        response = self._post_refresh(str(refresh))
        rotated_refresh_cookie = response.cookies[REFRESH_COOKIE_NAME].value

        self.assertTrue(rotated_refresh_cookie)
        self.assertNotEqual(rotated_refresh_cookie, str(refresh))

        # The new csrf_token pairs with the new cookie, not the old one.
        new_jti = extract_jti_unverified(rotated_refresh_cookie)
        self.assertEqual(response.data["csrf_token"], csrf_token_for_jti(new_jti))

        # The old refresh token was blacklisted by rotation - reusing it
        # (even with a valid CSRF pair) now fails.
        reuse_response = self._post_refresh(str(refresh))
        self.assertEqual(reuse_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_rejects_a_malformed_token_as_a_csrf_failure(self):
        # A token this broken has no readable jti at all, so there's no
        # CSRF value that could ever have paired with it - this is
        # rejected before validating the token is otherwise garbage.
        response = self._post_refresh("not-a-real-token")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_refresh_rejects_a_token_with_a_bad_signature(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)

        # Flips one character in the *middle* of the signature segment -
        # deliberately not the last character, since base64url's final
        # character carries padding bits that newer PyJWT versions
        # validate are canonical, which a naive last-character flip can
        # trip even before signature verification ever runs. A middle
        # character has no such constraint: the token stays the same
        # length and every segment stays valid base64url, so it decodes
        # fine unverified (a readable jti is what the CSRF check needs)
        # while its signature no longer matches.
        header, payload, signature = str(refresh).split(".")
        mid = len(signature) // 2
        replacement = "a" if signature[mid] != "a" else "b"
        tampered_signature = signature[:mid] + replacement + signature[mid + 1 :]
        tampered_token = f"{header}.{payload}.{tampered_signature}"

        response = self._post_refresh(tampered_token)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_rejects_a_deactivated_users_token(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        user.is_active = False
        user.save(update_fields=["is_active"])

        response = self._post_refresh(str(refresh))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_rejects_a_deleted_users_token(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        user.delete()

        response = self._post_refresh(str(refresh))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_without_a_cookie_returns_401(self):
        response = self.client.post(reverse("token_refresh"), HTTP_X_REFRESH_CSRF_TOKEN="anything")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_rejects_a_missing_csrf_header(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        self.client.cookies[REFRESH_COOKIE_NAME] = str(refresh)

        response = self.client.post(reverse("token_refresh"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_refresh_rejects_a_mismatched_csrf_header(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        set_refresh_cookie(self.client, str(refresh))

        response = self.client.post(
            reverse("token_refresh"), HTTP_X_REFRESH_CSRF_TOKEN="a-different-token"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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


class ProductionSecretKeyValidationTests(TestCase):
    """SECRET_KEY signs sessions, CSRF tokens, password reset/email
    verification links, and (via SimpleJWT's default) every JWT this API
    issues - settings.py refuses to start with DEBUG off unless it's been
    replaced with a real, sufficiently long value. This has to run Django's
    settings module fresh in a subprocess, since the validation happens at
    import time and the test process has already imported it once."""

    def _run_check(self, env_overrides):
        # A value of None means "unset this var" - needed because the CI
        # job itself sets DJANGO_SECRET_KEY at the step level, so simply
        # omitting it from env_overrides would leak that value through
        # os.environ instead of exercising the "not set at all" case.
        env = {**os.environ, "DJANGO_ALLOWED_HOSTS": "example.com", **env_overrides}
        env = {key: value for key, value in env.items() if value is not None}
        return subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=str(Path(__file__).resolve().parent.parent),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_refuses_the_default_dev_key_in_production(self):
        result = self._run_check({"DJANGO_DEBUG": "False", "DJANGO_SECRET_KEY": None})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)

    def test_refuses_a_short_key_in_production(self):
        result = self._run_check({"DJANGO_DEBUG": "False", "DJANGO_SECRET_KEY": "too-short"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("too short", result.stderr)

    def test_accepts_a_strong_key_in_production(self):
        result = self._run_check(
            {
                "DJANGO_DEBUG": "False",
                "DJANGO_SECRET_KEY": "a-properly-long-random-production-secret-key-1234567890",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_default_key_is_still_allowed_in_development(self):
        result = self._run_check({"DJANGO_DEBUG": "True", "DJANGO_SECRET_KEY": None})

        self.assertEqual(result.returncode, 0, result.stderr)


class CorsPreflightTests(APITestCase):
    """The double-submit CSRF header the frontend attaches on refresh/logout
    calls (accounts/cookies.py) has to be in CORS_ALLOW_HEADERS - otherwise
    the browser's own preflight blocks the request before Django ever sees
    it, no matter what the view allows. Curl and Django's test client don't
    enforce CORS themselves, so this has to check the preflight response
    headers directly rather than whether the real request succeeds."""

    def test_preflight_allows_the_refresh_csrf_header(self):
        response = self.client.options(
            reverse("token_refresh"),
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-refresh-csrf-token",
        )

        allowed_headers = response.get("Access-Control-Allow-Headers", "")
        self.assertIn("x-refresh-csrf-token", allowed_headers.lower())

    def test_preflight_allows_credentials(self):
        response = self.client.options(
            reverse("token_refresh"),
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )

        self.assertEqual(response.get("Access-Control-Allow-Credentials"), "true")
