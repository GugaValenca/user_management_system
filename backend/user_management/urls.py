from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from django.utils import timezone
import django


def root_status(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "user_management_system_api",
            "docs_hint": "/api/auth/",
            "admin": "/admin/",
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

urlpatterns = [
    path('', root_status, name='root_status'),
    path('health/', health_status, name='health_status'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
