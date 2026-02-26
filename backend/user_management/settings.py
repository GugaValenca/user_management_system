import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool) -> bool:
    raw = config(name, default=str(default))
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


SECRET_KEY = config("DJANGO_SECRET_KEY", default="django-insecure-dev-key")
DEBUG = env_bool("DJANGO_DEBUG", True)

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
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000",
    cast=Csv(),
)

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
