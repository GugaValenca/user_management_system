from datetime import timedelta

import django
from accounts.models import UserActivityLog
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.urls import include, path
from django.utils import timezone


def root_status(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "user_management_system_api",
            "docs_hint": "/api/auth/",
            "admin": "/admin/",
        }
    )


def api_status(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "user_management_system_api",
            "base_path": "/api/auth/",
            "health": "/health/",
            "auth_health": "/health/auth/",
        }
    )


def health_status(request):
    db_ok = True
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError as exc:
        db_ok = False
        db_error = str(exc)

    payload = {
        "status": "ok" if db_ok else "degraded",
        "service": "user_management_system_api",
        "timestamp_utc": timezone.now().isoformat(),
        "django_version": django.get_version(),
        "database": {
            "status": "ok" if db_ok else "error",
        },
    }
    if db_error:
        payload["database"]["error"] = db_error

    return JsonResponse(payload, status=200 if db_ok else 503)


def auth_health_status(request):
    db_ok = True
    db_error = None
    successful_logins_last_24h = 0
    last_successful_login = None
    now = timezone.now()
    since = now - timedelta(hours=24)

    try:
        successful_logins_last_24h = UserActivityLog.objects.filter(
            activity_type="login",
            timestamp__gte=since,
        ).count()
        last_successful_login = (
            UserActivityLog.objects.filter(activity_type="login")
            .order_by("-timestamp")
            .values_list("timestamp", flat=True)
            .first()
        )
    except OperationalError as exc:
        db_ok = False
        db_error = str(exc)

    payload = {
        "status": "ok" if db_ok else "degraded",
        "service": "user_management_system_api",
        "timestamp_utc": now.isoformat(),
        "auth": {
            "status": "ok" if db_ok else "error",
            "successful_logins_last_24h": successful_logins_last_24h,
            "last_successful_login_utc": (
                last_successful_login.isoformat() if last_successful_login else None
            ),
        },
    }
    if db_error:
        payload["auth"]["error"] = db_error

    return JsonResponse(payload, status=200 if db_ok else 503)


urlpatterns = [
    path("", root_status, name="root_status"),
    path("api/", api_status, name="api_status"),
    path("health/", health_status, name="health_status"),
    path("health/auth/", auth_health_status, name="auth_health_status"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
