from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("refresh/", views.ActiveUserTokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("password-reset/", views.request_password_reset, name="password_reset_request"),
    path(
        "password-reset/confirm/",
        views.confirm_password_reset,
        name="password_reset_confirm",
    ),
    path(
        "verify-email/confirm/",
        views.confirm_email_verification,
        name="verify_email_confirm",
    ),
    path(
        "verify-email/resend/",
        views.resend_email_verification,
        name="verify_email_resend",
    ),
    path("activity-logs/", views.UserActivityLogView.as_view(), name="activity_logs"),
    path("users/", views.AdminUserListView.as_view(), name="user_list"),
    path("users/<int:pk>/", views.AdminUserDetailView.as_view(), name="admin_user_detail"),
    path("stats/", views.user_stats, name="user_stats"),
]
