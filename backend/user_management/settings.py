from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from corsheaders.defaults import default_headers
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool) -> bool:
    raw = config(name, default=str(default))
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


SECRET_KEY = config("DJANGO_SECRET_KEY", default="django-insecure-dev-key")
DEBUG = env_bool("DJANGO_DEBUG", True)

# A weak or default SECRET_KEY is used to sign session cookies, the CSRF
# token, password reset/email verification tokens, and (via SimpleJWT's
# default HS256 signing key) every access and refresh token this API
# issues. Failing fast here means a misconfigured deploy never silently
# runs with a guessable key instead of quietly shipping a broken
# production environment.
if not DEBUG:
    if SECRET_KEY == "django-insecure-dev-key" or SECRET_KEY.startswith("django-insecure-"):
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set to a real, unique value in production."
        )
    if len(SECRET_KEY) < 32:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is too short for production use (need at least 32 characters)."
        )

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=Csv(),
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "accounts",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.AdminLoginRateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "user_management.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "user_management.wsgi.application"


def database_config_from_url(database_url: str):
    parsed = urlparse(database_url)
    scheme = parsed.scheme.lower()
    query = parse_qs(parsed.query)

    if scheme in {"postgres", "postgresql", "pgsql"}:
        db = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/") or "postgres",
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or 5432),
        }
        options = {}
        for key in ("sslmode", "channel_binding", "target_session_attrs"):
            if query.get(key):
                options[key] = query[key][0]
        if options:
            db["OPTIONS"] = options
        return {"default": db}

    if scheme == "mysql":
        return {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": parsed.path.lstrip("/") or "",
                "USER": parsed.username or "",
                "PASSWORD": parsed.password or "",
                "HOST": parsed.hostname or "localhost",
                "PORT": str(parsed.port or 3306),
            }
        }

    if scheme == "sqlite":
        sqlite_path = parsed.path or str(BASE_DIR / "db.sqlite3")
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": sqlite_path,
            }
        }

    raise ValueError(f"Unsupported DATABASE_URL scheme: {scheme}")


DATABASE_URL = config("DATABASE_URL", default="")
DB_ENGINE = config("DB_ENGINE", default="sqlite").lower()

if DATABASE_URL:
    DATABASES = database_config_from_url(DATABASE_URL)
elif DB_ENGINE in {"postgres", "postgresql"}:
    pg_db = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="postgres"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
    pg_options = {}
    db_sslmode = config("DB_SSLMODE", default="")
    db_channel_binding = config("DB_CHANNEL_BINDING", default="")
    if db_sslmode:
        pg_options["sslmode"] = db_sslmode
    if db_channel_binding:
        pg_options["channel_binding"] = db_channel_binding
    if pg_options:
        pg_db["OPTIONS"] = pg_options
    DATABASES = {"default": pg_db}
elif DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": config("DB_NAME", default="user_management_db"),
            "USER": config("DB_USER", default="root"),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="3306"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": config("SQLITE_PATH", default=str(BASE_DIR / "db.sqlite3")),
        }
    }

# Keep this in sync with PASSWORD_RESET_EXPIRY_HOURS in accounts/emails.py -
# it's what the reset email tells the user, this is what actually enforces it.
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "120/min",
        "login": "10/min",
        "register": "5/hour",
        "password_change": "10/hour",
        "password_reset": "5/hour",
        "email_verification": "5/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "accounts.exceptions.api_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "User Management System API",
    "DESCRIPTION": "JWT-based authentication and account management API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Email is used for password reset and account verification links. Defaults
# to printing messages to the console so the flow works out of the box in
# development; set EMAIL_BACKEND (and the SMTP settings below) in production.
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@user-management.local")

# Base URL of the deployed frontend, used to build links inside emails
# (e.g. https://user-management-site.vercel.app/reset-password).
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000").rstrip("/")

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
# The refresh token now travels in an httpOnly cookie (see accounts/cookies.py)
# instead of the response/request body, so the browser needs to be allowed to
# actually send it cross-origin. CORS_ALLOWED_ORIGINS stays a strict, exact
# allowlist (never a wildcard) - that's what makes credentialed CORS safe.
CORS_ALLOW_CREDENTIALS = True

# The double-submit CSRF header the frontend attaches on refresh/logout
# calls (see accounts/cookies.py) isn't in corsheaders' default allowlist -
# without this, the browser's own CORS preflight would block it before the
# request ever reached Django, regardless of what the view allows.
CORS_ALLOW_HEADERS = (*default_headers, "x-refresh-csrf-token")

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)

# The CSRF cookie only needs to be readable by Django's own admin templates
# (which embed the token server-side via {% csrf_token %}), never by
# frontend JS - blocking script access limits what a stray XSS could steal.
CSRF_COOKIE_HTTPONLY = True

# Cookie flags for the refresh-token cookie (accounts/cookies.py). The
# frontend and API live on different vercel.app subdomains, which the
# Public Suffix List treats as separate sites - SameSite=None is required
# for the cookie to be sent cross-site at all, and browsers only honor
# SameSite=None on cookies also marked Secure. Locally, frontend and
# backend differ only by port (same "site"), so Lax + non-Secure works
# over plain http.
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = "None" if not DEBUG else "Lax"

# Explicit rather than relying on Django's implicit 2.5MB default - this is
# a JSON API with no legitimate request anywhere near that size, and this
# app doesn't accept file uploads through this size check (profile picture
# uploads are validated separately, see accounts/validators.py).
DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024  # 1 MB

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
