from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from .models import User, UserActivityLog
from .tokens import email_verification_token

# Applied to every password input field. Generous for any real password,
# but keeps request bodies (and therefore hashing cost) bounded well below
# Django's global DATA_UPLOAD_MAX_MEMORY_SIZE - defense in depth, not the
# only thing standing between this API and an oversized-payload request.
PASSWORD_MAX_LENGTH = 128
IDENTIFIER_MAX_LENGTH = 254


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, max_length=PASSWORD_MAX_LENGTH, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(
        required=False, allow_blank=True, max_length=IDENTIFIER_MAX_LENGTH
    )
    identifier = serializers.CharField(
        required=False, allow_blank=True, max_length=IDENTIFIER_MAX_LENGTH
    )
    password = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)

    def validate(self, attrs):
        identifier = (attrs.get("identifier") or attrs.get("email") or "").strip()
        password = attrs.get("password")

        if not identifier or not password:
            raise serializers.ValidationError("Must include email/username and password")

        user = User.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier)
        ).first()

        # Run the hasher even when no user was found, so a nonexistent
        # identifier doesn't return measurably faster than a real one with a
        # wrong password - otherwise response timing alone lets an attacker
        # enumerate registered accounts despite the generic error message.
        if user is None:
            make_password(password)
            raise serializers.ValidationError("Invalid credentials")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        attrs["user"] = user

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "profile_picture",
            "phone_number",
            "date_of_birth",
            "bio",
            "is_email_verified",
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "is_email_verified",
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
        ]


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)
    new_password = serializers.CharField(
        write_only=True, max_length=PASSWORD_MAX_LENGTH, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("New passwords don't match")
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value


class UserActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = UserActivityLog
        fields = ["id", "user_email", "activity_type", "description", "ip_address", "timestamp"]
        read_only_fields = ["id", "timestamp"]


def _get_user_from_uid(uid):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=IDENTIFIER_MAX_LENGTH)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    new_password = serializers.CharField(
        write_only=True, max_length=PASSWORD_MAX_LENGTH, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, max_length=PASSWORD_MAX_LENGTH)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("Passwords don't match")

        user = _get_user_from_uid(attrs["uid"])
        if user is None or not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("This reset link is invalid or has expired")

        attrs["user"] = user
        return attrs


class EmailVerificationConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)

    def validate(self, attrs):
        user = _get_user_from_uid(attrs["uid"])
        if user is None or not email_verification_token.check_token(user, attrs["token"]):
            raise serializers.ValidationError("This verification link is invalid or has expired")

        attrs["user"] = user
        return attrs


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role", "is_active"]


# --- Response-only serializers, used solely to document API shapes that a
# function-based view builds by hand (drf-spectacular can't infer these). ---


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class AuthTokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user = UserProfileSerializer()
    tokens = AuthTokenPairSerializer()


class UserStatsResponseSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    admin_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
