from django.core.exceptions import ValidationError
from django.db import models


MAX_APK_SIZE_MB = 200
MAX_APK_SIZE_BYTES = MAX_APK_SIZE_MB * 1024 * 1024  # 200 MB


def validate_apk_size(file):
    """Reject APKs larger than MAX_APK_SIZE_MB."""
    if file.size > MAX_APK_SIZE_BYTES:
        raise ValidationError(
            f"APK file size must not exceed {MAX_APK_SIZE_MB} MB. "
            f"Current size: {file.size / (1024 * 1024):.1f} MB."
        )


def validate_apk_extension(file):
    """Ensure uploaded file has .apk extension."""
    if not file.name.lower().endswith(".apk"):
        raise ValidationError("Only .apk files are allowed.")


class AppUpdate(models.Model):
    """Represents a single APK release available for OTA update."""

    version = models.CharField(
        max_length=20,
        unique=True,
        help_text="Semantic version string, e.g. 1.2.0",
    )
    apk_file = models.FileField(
        upload_to="apks/",
        validators=[validate_apk_size, validate_apk_extension],
        help_text="Upload the APK file (max 200 MB).",
    )
    force_update = models.BooleanField(
        default=False,
        help_text="If True, the Flutter app must update before continuing.",
    )
    changelog = models.TextField(
        blank=True,
        help_text="What changed in this release (optional).",
    )
    min_supported_version = models.CharField(
        max_length=20,
        blank=True,
        help_text="Minimum app version that can update to this release (optional).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "App Update"
        verbose_name_plural = "App Updates"

    def __str__(self):
        return f"v{self.version}"
