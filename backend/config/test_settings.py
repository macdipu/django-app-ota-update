"""Test-only settings overriding DATABASE to use SQLite (no Postgres needed)."""
from config.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable whitenoise static file storage for tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Use local filesystem for file uploads in tests (Django 5 uses STORAGES).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": STATICFILES_STORAGE},
}
MEDIA_ROOT = "/tmp/ota_test_media"
