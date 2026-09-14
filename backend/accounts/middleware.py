from django.core.cache import cache
from django.http import HttpResponse

from .views import get_client_ip

# Django's own admin login view has no rate limiting - every login path in
# the custom API is throttled, but /admin/login/ was wide open to unlimited
# password guessing. This closes that gap with the same cache-based
# approach DRF's throttle classes already use elsewhere in this project,
# without pulling in a new dependency.
ADMIN_LOGIN_PATH = "/admin/login/"
ADMIN_LOGIN_MAX_ATTEMPTS = 10
ADMIN_LOGIN_WINDOW_SECONDS = 15 * 60


class AdminLoginRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path == ADMIN_LOGIN_PATH:
            key = f"admin-login-throttle:{get_client_ip(request)}"
            attempts = cache.get(key, 0)
            if attempts >= ADMIN_LOGIN_MAX_ATTEMPTS:
                return HttpResponse("Too many login attempts. Please try again later.", status=429)
            cache.set(key, attempts + 1, ADMIN_LOGIN_WINDOW_SECONDS)

        return self.get_response(request)
