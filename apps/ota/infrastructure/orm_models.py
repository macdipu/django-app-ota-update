"""
Infrastructure Layer — Django ORM Models.

This is the only layer that knows about Django's database ORM.
Two models live here:
  - MobileApp:  represents a registered mobile application (merchant, user, etc.)
  - AppUpdate:  represents a single APK release for a MobileApp.
"""
from django.core.exceptions import ValidationError
from django.db import models


MAX_APK_SIZE_MB = 500
MAX_APK_SIZE_BYTES = MAX_APK_SIZE_MB * 1024 * 1024  # 500 MB


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


class MobileApp(models.Model):
    """Represents a registered mobile application (e.g. Merchant App, User App)."""

    name = models.CharField(
        max_length=100,
        help_text="Human-readable app name, e.g. 'Merchant App'.",
    )
    package_name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Android package identifier, e.g. 'com.example.merchant'.",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional short description of this app.",
    )
    icon = models.ImageField(
        upload_to="app_icons/",
        blank=True,
        null=True,
        help_text="Optional app icon (PNG/JPG, recommended 512×512).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "ota"
        ordering = ["name"]
        verbose_name = "Mobile App"
        verbose_name_plural = "Mobile Apps"

    def __str__(self):
        return f"{self.name} ({self.package_name})"

    @property
    def latest_version(self):
        release = self.updates.order_by("-created_at").first()
        return release.version if release else "—"

    @property
    def release_count(self):
        return self.updates.count()


class AppUpdate(models.Model):
    """Django ORM model — persistence representation of an APK release."""

    app = models.ForeignKey(
        MobileApp,
        on_delete=models.CASCADE,
        related_name="updates",
        null=True,  # Allow null temporarily for safe migration
        blank=True,
        help_text="The mobile app this release belongs to.",
    )
    version = models.CharField(
        max_length=20,
        help_text="Semantic version string, e.g. 1.2.0",
    )
    apk_file = models.FileField(
        upload_to="apks/",
        validators=[validate_apk_size, validate_apk_extension],
        help_text="Upload the APK file (max 500 MB).",
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
        app_label = "ota"
        ordering = ["-created_at"]
        verbose_name = "App Release"
        verbose_name_plural = "App Releases"
        # version is unique per app (same version can exist for different apps)
        unique_together = [("app", "version")]

    def __str__(self):
        return f"{self.app.name} v{self.version}"
