"""
Domain Layer — Core Business Entities.

Pure Python only. No framework imports allowed.

Rule: This module may ONLY import from Python stdlib.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MobileAppEntity:
    """Immutable domain entity representing a registered mobile application."""

    id: int
    name: str
    package_name: str       # e.g. "com.example.merchant"
    description: str
    created_at: datetime


@dataclass(frozen=True)
class AppUpdateEntity:
    """Immutable domain entity representing a single APK release.

    Storage Design Note
    -------------------
    ``apk_file_path`` is a storage-relative path (e.g. "apks/app-v1.2.apk").
    It carries NO knowledge of HTTP, S3 URLs, or MEDIA_URL.
    The absolute download URL is resolved at the interface/presentation boundary
    so that switching storage backends (local → S3 → GCS) never touches this entity.
    """

    id: int
    app_id: int                     # FK → MobileAppEntity.id
    app_package_name: str
    public_id: str
    version: str
    build_number: int
    apk_file_path: str              # e.g. "apks/app-v1.2.apk"  (storage-agnostic)
    force_update: bool
    changelog: str
    min_supported_version: str
    created_at: datetime
