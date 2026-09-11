from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import email_verification_token

PASSWORD_RESET_EXPIRY_HOURS = 24


def _send_templated_email(subject, template_name, context, to_email):
    text_body = render_to_string(f"emails/{template_name}.txt", context)
    html_body = render_to_string(f"emails/{template_name}.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    _send_templated_email(
        subject="Reset your password",
        template_name="password_reset",
        context={
            "first_name": user.first_name or user.username,
            "reset_url": reset_url,
            "expiry_hours": PASSWORD_RESET_EXPIRY_HOURS,
        },
        to_email=user.email,
    )


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"

    _send_templated_email(
        subject="Verify your email address",
        template_name="verify_email",
        context={
            "first_name": user.first_name or user.username,
            "verify_url": verify_url,
        },
        to_email=user.email,
    )
