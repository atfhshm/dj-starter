"""
Django settings for core project.
"""

import ssl
from pathlib import Path

import dj_database_url
import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from core.logging import build_logging_config, configure_structlog
from core.openapi import OPENAPI_SETTINGS

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------
# ENV Reader
# ----------

ENV = environ.Env()
ENV.read_env(BASE_DIR / ".env")


def _parse_contact_list(value: str) -> list[tuple[str, str]]:
    """Parse ``Name:email@example.com,Name2:email2@example.com`` for ADMINS/MANAGERS."""
    if not value:
        return []
    contacts: list[tuple[str, str]] = []
    for entry in value.split(","):
        name, email = entry.strip().rsplit(":", 1)
        contacts.append((name.strip(), email.strip()))
    return contacts


# -----------
# Base Config
# -----------

DEBUG = ENV("DEBUG", cast=bool, default=True)
SECRET_KEY = ENV("SECRET_KEY", cast=str, default="some-random-secret-key")

# -------------
# Allowed hosts
# -------------

ALLOWED_HOSTS = ENV("ALLOWED_HOSTS", cast=list, default=["*"])


# -------------
# CORS settings
# -------------

CORS_ALLOWED_ORIGINS = ENV(
    "CORS_ALLOWED_ORIGINS",
    cast=list,
    default=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
)

CORS_ALLOW_CREDENTIALS = ENV(
    "CORS_ALLOW_CREDENTIALS",
    cast=bool,
    default=True,
)

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "accept-language",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-request-id",
    "x-correlation-id",
]

CORS_EXPOSE_HEADERS = [
    "X-Request-ID",
    "X-Correlation-ID",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# --------------
# HTTPS settings
# --------------

SECURE_SSL_REDIRECT = ENV(
    "SECURE_SSL_REDIRECT",
    cast=bool,
    default=not DEBUG,
)
SECURE_PROXY_SSL_HEADER = ENV(
    "SECURE_PROXY_SSL_HEADER",
    cast=tuple,
    default=("HTTP_X_FORWARDED_PROTO", "https"),
)
SECURE_HSTS_SECONDS = ENV(
    "SECURE_HSTS_SECONDS",
    cast=int,
    default=31536000 if not DEBUG else 0,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = ENV(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    cast=bool,
    default=not DEBUG,
)
SECURE_HSTS_PRELOAD = ENV(
    "SECURE_HSTS_PRELOAD",
    cast=bool,
    default=not DEBUG,
)
SECURE_CONTENT_TYPE_NOSNIFF = ENV(
    "SECURE_CONTENT_TYPE_NOSNIFF",
    cast=bool,
    default=True,
)
SECURE_BROWSER_XSS_FILTER = ENV(
    "SECURE_BROWSER_XSS_FILTER",
    cast=bool,
    default=True,
)
SECURE_REFERRER_POLICY = ENV(
    "SECURE_REFERRER_POLICY",
    cast=str,
    default="strict-origin-when-cross-origin",
)

# -----------------------
# Application definitions
# -----------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "django_structlog",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "phonenumber_field",
    "django_celery_beat",
    "django_celery_results",
    "django_countries",
]

LOCAL_APPS = [
    "core.apps.CoreConfig",
    "user.apps.UserConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# -----------
# Middlewares
# -----------

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "core.middlewares.TraceMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middlewares.TimezoneMiddleware",
    "core.middlewares.LocaleMiddleware",
    "core.middlewares.URL404Middleware",
]

# -------------
# Root URLconf
# -------------

ROOT_URLCONF = "core.urls"
APPEND_SLASH = False

# ---------
# Templates
# ---------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# -------------
# WSGI and ASGI
# -------------

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# ---------------
# Database config
# ---------------

# the default auto field for all models
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASE_URL = ENV("DATABASE_URL", cast=str)

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    ),
}

# ------------
# Redis config
# ------------
REDIS_URL = ENV("REDIS_URL", cast=str)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100,
                "retry_on_timeout": True,
            },
        },
    }
}

# -------------
# Celery config
# -------------

CELERY_BROKER_URL = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

# Only enable broker TLS when the broker URL actually uses a TLS scheme
if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
    }

# ---------------------
# Celery Beat and Results Config
# ---------------------

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_EXTENDED = True


# ---------------
# Channels Config
# ---------------

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# -------------------
# Password validation
# -------------------

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

# ----------------
# Password hashers
# ----------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# -------------
# Auth Settings
# -------------

AUTH_USER_MODEL = "user.User"


# ---------------------
# Auth Session Settings
# ---------------------

SESSION_COOKIE_NAME = ENV("SESSION_COOKIE_NAME", cast=str, default="session-id")
SESSION_COOKIE_AGE = ENV("SESSION_COOKIE_AGE", cast=int, default=60 * 60 * 24 * 30)
SESSION_COOKIE_HTTPONLY = ENV("SESSION_COOKIE_HTTPONLY", cast=bool, default=True)
SESSION_COOKIE_PATH = ENV("SESSION_COOKIE_PATH", cast=str, default="/")
SESSION_COOKIE_SAMESITE = ENV("SESSION_COOKIE_SAMESITE", cast=str, default="Lax")
SESSION_COOKIE_SECURE = ENV("SESSION_COOKIE_SECURE", cast=bool, default=not DEBUG)

# -------------
# CSRF Settings
# -------------
CSRF_TRUSTED_ORIGINS = ENV(
    "CSRF_TRUSTED_ORIGINS",
    cast=list,
    default=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
)
CSRF_COOKIE_SECURE = ENV("CSRF_COOKIE_SECURE", cast=bool, default=not DEBUG)
CSRF_COOKIE_HTTPONLY = ENV("CSRF_COOKIE_HTTPONLY", cast=bool, default=False)
CSRF_COOKIE_SAMESITE = ENV("CSRF_COOKIE_SAMESITE", cast=str, default="Lax")

# -----------------------
# REST Framework Settings
# -----------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.app_error_handler",
    "NON_FIELD_ERRORS_KEY": "detail",
    # Dates
    "DATETIME_FORMAT": "iso-8601",
    "DATE_FORMAT": "iso-8601",
    "TIME_FORMAT": "iso-8601",
    # Formatting
    "URL_FORMAT_OVERRIDE": None,
    "COERCE_DECIMAL_TO_STRING": True,
    "UPLOADED_FILES_USE_URL": True,
}

# ----------------
# OpenAPI Settings
# ----------------

ENABLE_OPENAPI = ENV("ENABLE_OPENAPI", cast=bool, default=True)

SPECTACULAR_SETTINGS = OPENAPI_SETTINGS

# --------------
# Storage config
# --------------

ACCESS_KEY_ID = ENV("ACCESS_KEY_ID", cast=str)
SECRET_ACCESS_KEY = ENV("SECRET_ACCESS_KEY", cast=str)
STORAGE_BUCKET_NAME = ENV("STORAGE_BUCKET_NAME", cast=str)
REGION_NAME = ENV("REGION_NAME", cast=str)
ENDPOINT_URL = ENV("ENDPOINT_URL", cast=str)
STATIC_STORAGE_CUSTOM_DOMAIN = ENV("STATIC_STORAGE_CUSTOM_DOMAIN", cast=str, default="")
SIGNATURE_VERSION = "s3v4"


BASE_STORAGE_OPTIONS = {
    "access_key": ACCESS_KEY_ID,
    "secret_key": SECRET_ACCESS_KEY,
    "bucket_name": STORAGE_BUCKET_NAME,
    "endpoint_url": ENDPOINT_URL,
    "signature_version": SIGNATURE_VERSION,
    # "region_name": REGION_NAME,
}

DEFAULT_STORAGE_OPTIONS = {
    **BASE_STORAGE_OPTIONS,
    "file_overwrite": False,
    "default_acl": "private",
    "object_parameters": {
        "CacheControl": "max-age=86400",
    },
}

STATICFILES_STORAGE_OPTIONS = {
    **BASE_STORAGE_OPTIONS,
}

if STATIC_STORAGE_CUSTOM_DOMAIN:
    # Serve collected static files from a public bucket/CDN domain (e.g. an R2
    # public dev URL) with clean, unsigned URLs instead of signed endpoint URLs.
    STATICFILES_STORAGE_OPTIONS["custom_domain"] = STATIC_STORAGE_CUSTOM_DOMAIN
    STATICFILES_STORAGE_OPTIONS["querystring_auth"] = False

STORAGES = {
    "default": {
        "BACKEND": "core.storage.UploadsStorage",
        "OPTIONS": DEFAULT_STORAGE_OPTIONS,
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": STATICFILES_STORAGE_OPTIONS,
    },
}

# --------------
# Email settings
# --------------

ADMINS = ENV("ADMINS", cast=_parse_contact_list, default=[])
MANAGERS = ENV("MANAGERS", cast=_parse_contact_list, default=[])

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = ENV("EMAIL_HOST", cast=str)
EMAIL_PORT = ENV("EMAIL_PORT", cast=int)
EMAIL_HOST_USER = ENV("EMAIL_HOST_USER", cast=str)
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", cast=str)
EMAIL_USE_TLS = ENV("EMAIL_USE_TLS", cast=bool, default=True)
EMAIL_USE_SSL = ENV("EMAIL_USE_SSL", cast=bool, default=False)
EMAIL_TIMEOUT = ENV("EMAIL_TIMEOUT", cast=int, default=10)
DEFAULT_FROM_EMAIL = ENV("DEFAULT_FROM_EMAIL", cast=str, default="noreply@example.com")
SERVER_EMAIL = ENV("SERVER_EMAIL", cast=str, default="noreply@example.com")
EMAIL_SUBJECT_PREFIX = ENV("EMAIL_SUBJECT_PREFIX", cast=str, default="[Django]")

# ---------------
# i18n / Timezone
# ---------------

# http://www.lingoes.net/en/translator/langcode.htm
LANGUAGE_CODE = "en-US"
LANGUAGES: list[tuple[str, str]] = [
    ("en-US", "English (United States)"),
    ("ar-EG", "Arabic (Egypt)"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------
# Site settings
# -------------

SITE_ID = 1

# --------------------
# File Upload settings
# --------------------

FILE_UPLOAD_MAX_MEMORY_SIZE = ENV(
    "FILE_UPLOAD_MAX_MEMORY_SIZE",
    cast=int,
    default=1024 * 1024 * 15,  # Defaults to 15MB
)

DATA_UPLOAD_MAX_NUMBER_FIELDS = ENV(
    "DATA_UPLOAD_MAX_NUMBER_FIELDS",
    cast=int,
    default=1000,
)

DATA_UPLOAD_MAX_MEMORY_SIZE = ENV(
    "DATA_UPLOAD_MAX_MEMORY_SIZE",
    cast=int,
    default=1024 * 1024 * 10,  # 10MB
)

# ------------
# Static files
# ------------

STATICFILES_DIRS = [BASE_DIR.joinpath("static/")]

STATIC_URL = "static/"
MEDIA_URL = "uploads/"

# -----------
# Media files
# -----------

MEDIA_ROOT = BASE_DIR.joinpath("uploads/")
STATIC_ROOT = BASE_DIR.joinpath("staticfiles/")

# -------------
# Silk settings
# -------------

SILK_ENABLED = DEBUG and ENV("SILK_ENABLED", cast=bool, default=True)
if SILK_ENABLED:
    INSTALLED_APPS.append("silk")
    MIDDLEWARE.append("silk.middleware.SilkyMiddleware")

# -------
# Logging
# -------
LOG_LEVEL = ENV("LOG_LEVEL", cast=str, default="INFO")
LOGGING = build_logging_config(
    debug=DEBUG,
    log_level=LOG_LEVEL,
)
configure_structlog()

# -------------
# Sentry config
# -------------

SENTRY_DSN = ENV("SENTRY_DSN", cast=str, default="")
if SENTRY_DSN:
    SENTRY_ENVIRONMENT = ENV("SENTRY_ENVIRONMENT", cast=str)
    SENTRY_TRACES_SAMPLE_RATE = ENV("SENTRY_TRACES_SAMPLE_RATE", cast=float, default=1.0)
    SENTRY_SAMPLE_RATE = ENV("SENTRY_SAMPLE_RATE", cast=float, default=1.0)

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        sample_rate=SENTRY_SAMPLE_RATE,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        integrations=[DjangoIntegration()],
    )
