import hashlib
import hmac
import secrets

from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

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
# on the victim's cookie for free.
#
# The textbook fix is a second, JS-readable "double-submit" cookie whose
# value the frontend echoes back in a header - but the frontend and API
# here live on different vercel.app subdomains, which browsers treat as
# entirely separate origins with separate cookie jars. A cookie the API
# sets is simply invisible to JavaScript running on the frontend's page;
# there's no cookie to double-submit.
#
# Instead, the CSRF token is derived deterministically from the refresh
# token's own jti via HMAC, and handed to the frontend once, in the same
# JSON response body that carries the access token (readable by the
# frontend's own JS, not by a forged cross-site request - CORS blocks
# that regardless of cookies). The frontend keeps it in memory and echoes
# it back as a header on refresh/logout. The server never has to store
# anything to check it: it just recomputes the HMAC from the refresh
# cookie's jti and compares. A forged request carries the victim's cookie
# automatically, but has no way to have ever learned the matching token.
CSRF_HEADER_NAME = "HTTP_X_REFRESH_CSRF_TOKEN"


def _cookie_kwargs(max_age_seconds):
    return {
        "max_age": max_age_seconds,
        "path": COOKIE_PATH,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
    }


def set_refresh_cookie(response, refresh_token, max_age_seconds):
    response.set_cookie(
        REFRESH_COOKIE_NAME, refresh_token, httponly=True, **_cookie_kwargs(max_age_seconds)
    )


def clear_refresh_cookie(response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path=COOKIE_PATH)


def csrf_token_for_jti(jti):
    return hmac.new(settings.SECRET_KEY.encode(), str(jti).encode(), hashlib.sha256).hexdigest()


def extract_jti_unverified(token_str):
    """Reads the jti claim out of a refresh token string without checking
    its signature, expiry, or blacklist status - only ever used to look up
    which CSRF token *should* pair with this cookie, never to authorize
    anything by itself. An attacker can't turn this into a bypass: forging
    a jti doesn't help without the secret key needed to HMAC it, and the
    token still goes through full verification afterward before it's
    actually honored."""
    try:
        return str(RefreshToken(token_str, verify=False)["jti"])
    except Exception:
        return None


def csrf_check_passes(request, jti):
    header_value = request.META.get(CSRF_HEADER_NAME)
    if not header_value or not jti:
        return False
    return secrets.compare_digest(csrf_token_for_jti(jti), header_value)
