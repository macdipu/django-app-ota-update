import os
from pathlib import Path
from core.logging import LOGGING

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(key: str, default: bool = False) -> bool:
    """Parse common truthy strings from environment variables."""
    return os.getenv(key, str(default)).lower() in {"1", "true", "t", "yes", "y", "on"}

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret-change-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# ---------------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "drf_spectacular",
    # Project apps
    "apps.ota.apps.OtaConfig",
]

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "ota_db"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & Media files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Optional: use MinIO (or any S3-compatible) for media storage
INSTALLED_APPS += ["storages"]
DEFAULT_FILE_STORAGE = "apps.ota.infrastructure.storage.PublicRewritingS3Boto3Storage"

AWS_STORAGE_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "ota-media")
AWS_S3_ENDPOINT_URL = os.getenv("MINIO_ENDPOINT_URL", "http://localhost:9000").rstrip("/")
AWS_ACCESS_KEY_ID = os.getenv("MINIO_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("MINIO_SECRET_KEY", "")
AWS_S3_REGION_NAME = os.getenv("MINIO_REGION_NAME", "us-east-1")
AWS_S3_ADDRESSING_STYLE = os.getenv("MINIO_ADDRESSING_STYLE", "path")
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_USE_SSL = env_bool("MINIO_USE_SSL", False)
AWS_QUERYSTRING_AUTH = True

MEDIA_URL = os.getenv("MEDIA_URL", f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/")

# Optional override for public-facing media host (e.g., when storage endpoint is not directly reachable by clients)
MEDIA_PUBLIC_BASE_URL = os.getenv("MEDIA_PUBLIC_BASE_URL", "").rstrip("/")

# Django 5 uses STORAGES; ensure media files go to MinIO instead of local FS.
STORAGES = {
    "default": {"BACKEND": "apps.ota.infrastructure.storage.PublicRewritingS3Boto3Storage"},
    "staticfiles": {"BACKEND": STATICFILES_STORAGE},
}

# ---------------------------------------------------------------------------
# Default primary key
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Migration modules — Clean Architecture: migrations live in infrastructure/
# ---------------------------------------------------------------------------
MIGRATION_MODULES = {
    "ota": "apps.ota.infrastructure.migrations",
}


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

# ---------------------------------------------------------------------------
# API Documentation (drf-spectacular)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "Android OTA Update API",
    "DESCRIPTION": (
        "Backend for managing Android Over-the-Air (OTA) APK updates. "
        "Provides endpoints for the Flutter app to check for and download the latest release."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------------------
# Optional: simple API key authentication
# Set API_KEY in .env to enable; leave blank to allow open access.
# ---------------------------------------------------------------------------
OTA_API_KEY = os.getenv("API_KEY", "")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = LOGGING
