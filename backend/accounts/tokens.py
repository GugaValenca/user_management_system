from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Same mechanism as Django's password reset tokens (HMAC over user state +
    timestamp, no extra DB table), but salted differently so a verification
    link can never be replayed as a password reset link or vice versa, and
    keyed off is_email_verified instead of the password hash so verifying
    doesn't get invalidated by an unrelated password change.
    """

    key_salt = "accounts.tokens.EmailVerificationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_email_verified}{timestamp}"


email_verification_token = EmailVerificationTokenGenerator()
