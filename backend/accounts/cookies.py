import secrets

from django.conf import settings

# The refresh token used to travel in the JSON response/request body,
# alongside the access token, and the frontend kept both in localStorage -
# meaning any XSS anywhere in the app could read a long-lived (7 day)
# credential straight out of browser storage. It now lives only in an
# httpOnly cookie, invisible to JavaScript, scoped narrowly to the auth
# endpoints that actually need it.
REFRESH_COOKIE_NAME = "refresh_token"
COOKIE_PATH = "/api/auth/"

# httpOnly protects the refresh token from XSS, but a cookie sent
# automatically by the browser is exactly what CSRF exploits - a forged
# cross-site request to /refresh/ or /logout/ would otherwise ride along
# on the victim's cookie for free. This is the standard double-submit
# pattern: a second, JS-readable cookie whose value the frontend must echo
# back in a custom header. Only same-origin JS can read the cookie to
# produce a match, which a cross-site form/fetch can't fake.
CSRF_COOKIE_NAME = "refresh_csrf_token"
CSRF_HEADER_NAME = "HTTP_X_REFRESH_CSRF_TOKEN"


def _cookie_kwargs(max_age_seconds):
    return {
        "max_age": max_age_seconds,
        "path": COOKIE_PATH,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }


def generate_csrf_token():
    return secrets.token_urlsafe(32)


def set_refresh_cookies(response, refresh_token, max_age_seconds):
    """Sets the httpOnly refresh-token cookie and its matching CSRF
    double-submit cookie. Returns nothing - both cookies are attached
    directly to the given response."""
    response.set_cookie(
        REFRESH_COOKIE_NAME, refresh_token, httponly=True, **_cookie_kwargs(max_age_seconds)
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        generate_csrf_token(),
        httponly=False,
        **_cookie_kwargs(max_age_seconds),
    )


def clear_refresh_cookies(response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path=COOKIE_PATH)
    response.delete_cookie(CSRF_COOKIE_NAME, path=COOKIE_PATH)


def csrf_check_passes(request):
    cookie_value = request.COOKIES.get(CSRF_COOKIE_NAME)
    header_value = request.META.get(CSRF_HEADER_NAME)
    if not cookie_value or not header_value:
        return False
    return secrets.compare_digest(cookie_value, header_value)
