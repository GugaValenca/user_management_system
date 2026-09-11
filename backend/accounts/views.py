from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import send_password_reset_email, send_verification_email
from .models import User, UserActivityLog
from .permissions import IsAdmin
from .serializers import (
    AdminUserUpdateSerializer,
    AuthResponseSerializer,
    EmailVerificationConfirmSerializer,
    ErrorResponseSerializer,
    MessageResponseSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserActivityLogSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserStatsResponseSerializer,
)


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"


class PasswordChangeRateThrottle(UserRateThrottle):
    scope = "password_change"


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = "password_reset"


class EmailVerificationRateThrottle(UserRateThrottle):
    scope = "email_verification"


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def log_user_activity(user, activity_type, description, request):
    UserActivityLog.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def blacklist_all_tokens_for(user):
    """Force every existing refresh token for this user to be re-issued via
    login - used after a password reset, since a leaked old password
    shouldn't leave old sessions valid."""
    for outstanding_token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=outstanding_token)


@extend_schema(
    request=UserRegistrationSerializer,
    responses={201: AuthResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register_user(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            user = serializer.save()
            log_user_activity(user, "register", "User registered successfully", request)

            refresh = RefreshToken.for_user(user)
            response_data = {
                "message": "User created successfully",
                "user": UserProfileSerializer(user).data,
                "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
            }

        # Sent outside the transaction so a slow/broken email provider can
        # never roll back an otherwise-successful registration.
        try:
            send_verification_email(user)
        except Exception:
            pass

        return Response(response_data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=UserLoginSerializer,
    responses={200: AuthResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_user(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]

        # Django's session-based login() would normally update last_login and
        # start a session; we only use JWTs here, so update it manually instead.
        user.last_login = timezone.now()
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=["last_login", "last_login_ip"])

        log_user_activity(user, "login", "User logged in successfully", request)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Login successful",
                "user": UserProfileSerializer(user).data,
                "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
            }
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request={
        "application/json": {"type": "object", "properties": {"refresh_token": {"type": "string"}}}
    },
    responses={200: MessageResponseSerializer, 400: ErrorResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "refresh_token is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        token = RefreshToken(refresh_token)
        token.blacklist()

        log_user_activity(request.user, "logout", "User logged out successfully", request)
        return Response({"message": "Logout successful"})
    except TokenError:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            log_user_activity(
                request.user, "profile_update", "Profile updated successfully", request
            )
        return response


@extend_schema(
    request=PasswordChangeSerializer,
    responses={200: MessageResponseSerializer, 400: PasswordChangeSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([PasswordChangeRateThrottle])
def change_password(request):
    serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        log_user_activity(user, "password_change", "Password changed successfully", request)

        return Response({"message": "Password changed successfully"})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=PasswordResetRequestSerializer,
    responses={200: MessageResponseSerializer},
    description=(
        "Always returns the same generic response whether or not the email "
        "is registered, to avoid leaking which addresses have accounts."
    ),
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def request_password_reset(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
    if user and user.is_active:
        try:
            send_password_reset_email(user)
        except Exception:
            pass

    return Response({"message": "If an account exists for that email, a reset link has been sent."})


@extend_schema(
    request=PasswordResetConfirmSerializer,
    responses={200: MessageResponseSerializer, 400: MessageResponseSerializer},
    description="uid and token come from the link sent by the password reset request email.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def confirm_password_reset(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    user.set_password(serializer.validated_data["new_password"])
    user.save()
    blacklist_all_tokens_for(user)

    log_user_activity(user, "password_reset", "Password reset via email link", request)

    return Response({"message": "Password reset successfully. Please log in again."})


@extend_schema(
    request=EmailVerificationConfirmSerializer,
    responses={200: MessageResponseSerializer, 400: MessageResponseSerializer},
    description="uid and token come from the link sent by the verification email.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([EmailVerificationRateThrottle])
def confirm_email_verification(request):
    serializer = EmailVerificationConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        log_user_activity(user, "email_verified", "Email address verified", request)

    return Response({"message": "Email verified successfully."})


@extend_schema(
    request=None,
    responses={200: MessageResponseSerializer, 502: ErrorResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([EmailVerificationRateThrottle])
def resend_email_verification(request):
    user = request.user
    if user.is_email_verified:
        return Response({"message": "Email is already verified."})

    try:
        send_verification_email(user)
    except Exception:
        return Response(
            {"error": "Could not send verification email. Please try again later."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({"message": "Verification email sent."})


class UserActivityLogView(generics.ListAPIView):
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserActivityLog.objects.filter(user=self.request.user)


@extend_schema(
    parameters=[
        OpenApiParameter(
            "search", str, description="Matches against email, username, first/last name."
        ),
        OpenApiParameter("role", str, description="Exact match: admin, moderator, or user."),
        OpenApiParameter("is_active", str, description="'true' or 'false'."),
    ]
)
class AdminUserListView(generics.ListAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = User.objects.all().order_by("-created_at")

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        role = self.request.query_params.get("role", "").strip()
        if role:
            queryset = queryset.filter(role=role)

        is_active = self.request.query_params.get("is_active", "").strip().lower()
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=(is_active == "true"))

        return queryset


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """Lets an admin change another user's role or activate/deactivate their
    account. Deliberately can't be used on your own account, so an admin can
    never accidentally lock themselves out or strand the account with no
    other admin able to restore it."""

    queryset = User.objects.all()
    serializer_class = AdminUserUpdateSerializer
    permission_classes = [IsAdmin]

    def get_object(self):
        obj = super().get_object()
        if obj.pk == self.request.user.pk:
            raise PermissionDenied("You can't change your own role or active status here.")
        return obj

    def perform_update(self, serializer):
        target_user = serializer.instance
        previous_role, previous_active = target_user.role, target_user.is_active

        serializer.save()

        changes = []
        if target_user.role != previous_role:
            changes.append(f"role changed to {target_user.role}")
        if target_user.is_active != previous_active:
            changes.append("activated" if target_user.is_active else "deactivated")

        if changes:
            description = (
                f"Account updated by admin {self.request.user.email}: {', '.join(changes)}"
            )
            log_user_activity(target_user, "admin_update", description, self.request)


@extend_schema(responses={200: UserStatsResponseSerializer})
@api_view(["GET"])
@permission_classes([IsAdmin])
def user_stats(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(role="admin").count()

    return Response(
        {
            "total_users": total_users,
            "active_users": active_users,
            "admin_users": admin_users,
            "inactive_users": total_users - active_users,
        }
    )
