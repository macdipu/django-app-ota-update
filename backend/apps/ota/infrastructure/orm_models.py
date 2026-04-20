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
    # A per-app counter used to allocate build numbers atomically.
    last_build_number = models.IntegerField(
        default=0,
        help_text="Last allocated build number for this app (used for atomic allocation).",
    )

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
    # Per-app, auto-incrementing build number (integer). Computed on save if missing.
    build_number = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Integer build number auto-incremented per app (read-only).",
    )
    # Public opaque id used in external download URLs to avoid exposing numeric ids
    public_id = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        unique=True,
        help_text="Opaque UUID used in public download URLs.",
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
        unique_together = [("app", "version"), ("app", "build_number")]

    def __str__(self):
        return f"{self.app.name} v{self.version}"

    def save(self, *args, **kwargs):
        # Compute checksum once when file present and checksum missing.
        if self.apk_file and not self.checksum_sha256:
            hasher = hashlib.sha256()
            for chunk in self.apk_file.chunks():
                hasher.update(chunk)
            self.checksum_sha256 = hasher.hexdigest()

        # Ensure a per-app build_number is assigned when missing.
        if self.build_number is None:
            # Prefer an atomic allocation using a per-app counter to avoid races.
            try:
                from django.db import transaction

                if self.app_id:
                    # Lock the MobileApp row and increment its counter atomically.
                    with transaction.atomic():
                        app_row = MobileApp.objects.select_for_update().get(pk=self.app_id)
                        app_row.last_build_number = (app_row.last_build_number or 0) + 1
                        app_row.save(update_fields=["last_build_number"])
                        # Refresh to be sure we have the persisted value
                        app_row.refresh_from_db()
                        self.build_number = app_row.last_build_number
                else:
                    # No app associated; fallback to Max+1 behavior
                    from django.db.models import Max

                    max_bn = (
                        AppUpdate.objects.filter(app_id=self.app_id)
                        .aggregate(Max("build_number"))
                        .get("build_number__max")
                    )
                    self.build_number = (max_bn or 0) + 1
            except Exception:
                # In case of any DB issues (e.g., missing table during migrate), fallback to 1
                if not self.build_number:
                    self.build_number = 1

        # Ensure a public_id exists (opaque UUID). Use uuid4 hex if missing.
        if not self.public_id:
            try:
                # generate a UUID4 string
                from uuid import uuid4

                self.public_id = str(uuid4())
            except Exception:
                # fallback to a short random string
                self.public_id = uuid4().hex if 'uuid4' in globals() else None

        super().save(*args, **kwargs)

    # upload path handled by module-level apk_upload_path
