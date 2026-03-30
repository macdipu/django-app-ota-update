"""
Infrastructure Layer — Django ORM Models.

This is the only layer that knows about Django's database ORM.
Two models live here:
  - MobileApp:  represents a registered mobile application (merchant, user, etc.)
  - AppUpdate:  represents a single APK release for a MobileApp.
"""
from django.core.exceptions import ValidationError
from django.db import models
import hashlib
from pathlib import Path
from uuid import uuid4
import random
import string

from django.utils.text import slugify


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


def apk_upload_path(instance, filename: str) -> str:
    """Generate a unique, collision-resistant upload path.

    Structure: apks/<project_name>/<project_name>_<version>_<unique>.apk
    Where unique is 6 random letters.
    Falls back gracefully if app or version are missing.
    """
    ext = Path(filename).suffix or ".apk"
    project_name = "app"
    app = getattr(instance, "app", None)
    if app:
        # Use package_name or name, replace dots and spaces with underscores
        project_name = (app.package_name or app.name).replace('.', '_').replace(' ', '_') or f"app_{app.pk or 'unknown'}"

    version_part = (slugify(getattr(instance, "version", "")) or "v").replace('-', '_')
    unique = ''.join(random.choices(string.ascii_letters, k=6))
    file_name = f"{project_name}_{version_part}_{unique}{ext}"
    return f"apks/{project_name}/{file_name}"


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
        upload_to=apk_upload_path,
        validators=[validate_apk_size, validate_apk_extension],
        help_text="Upload the APK file (max 500 MB).",
    )
    checksum_sha256 = models.CharField(
        max_length=64,
        blank=True,
        help_text="Integrity checksum of the uploaded APK (SHA-256).",
    )
    is_pinned = models.BooleanField(
        default=False,
        help_text="If True, treat this release as pinned/promoted regardless of recency.",
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

    def save(self, *args, **kwargs):
        # Compute checksum once when file present and checksum missing.
        if self.apk_file and not self.checksum_sha256:
            hasher = hashlib.sha256()
            for chunk in self.apk_file.chunks():
                hasher.update(chunk)
            self.checksum_sha256 = hasher.hexdigest()
        super().save(*args, **kwargs)

    # upload path handled by module-level apk_upload_path
