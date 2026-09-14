import logging
from datetime import timedelta

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.urls import include, path
from django.utils import timezone
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from accounts.models import UserActivityLog

logger = logging.getLogger(__name__)


def root_status(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "user_management_system_api",
            "docs_hint": "/api/docs/",
        }
    )


def api_status(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "user_management_system_api",
            "base_path": "/api/auth/",
            "docs": "/api/docs/",
            "health": "/health/",
            "auth_health": "/health/auth/",
        }
    )


def health_status(request):
    # This endpoint is public and unauthenticated (it's what uptime monitors
    # hit), so the raw exception text never goes in the response - a bare
    # OperationalError can include the DB host, port, or other internal
    # infrastructure details. The full exception is still logged
    # server-side for whoever is actually debugging an outage.
    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError:
        db_ok = False
        logger.exception("Health check database query failed")

    payload = {
        "status": "ok" if db_ok else "degraded",
        "service": "user_management_system_api",
        "timestamp_utc": timezone.now().isoformat(),
        "database": {
            "status": "ok" if db_ok else "error",
        },
    }

    return JsonResponse(payload, status=200 if db_ok else 503)


def auth_health_status(request):
    # Same reasoning as health_status above: no raw exception text in the
    # public response, full detail goes to the server log instead.
    db_ok = True
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
    except OperationalError:
        db_ok = False
        logger.exception("Auth health check database query failed")

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

    return JsonResponse(payload, status=200 if db_ok else 503)


urlpatterns = [
    path("", root_status, name="root_status"),
    path("api/", api_status, name="api_status"),
    path("health/", health_status, name="health_status"),
    path("health/auth/", auth_health_status, name="auth_health_status"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger_ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
