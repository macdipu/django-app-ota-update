"""
Infrastructure Layer — Concrete Django ORM Repositories.

Implements the AppRepository and UpdateRepository Protocols from the domain layer.
Translates ORM model instances → domain entities.

Rule: May import from domain layer and Django ORM only.
"""
from typing import Optional

from apps.ota.domain.entities import AppUpdateEntity, MobileAppEntity
from apps.ota.domain.repositories import AppRepository, UpdateRepository
from apps.ota.infrastructure.orm_models import AppUpdate, MobileApp


class DjangoAppRepository:
    """Fetches MobileApp records and maps them to domain entities."""

    def _to_entity(self, orm_obj: MobileApp) -> MobileAppEntity:
        return MobileAppEntity(
            id=orm_obj.pk,
            name=orm_obj.name,
            package_name=orm_obj.package_name,
            description=orm_obj.description,
            created_at=orm_obj.created_at,
        )

    def get_all_apps(self) -> list[MobileAppEntity]:
        return [self._to_entity(obj) for obj in MobileApp.objects.all()]

    def get_app_by_package(self, package_name: str) -> Optional[MobileAppEntity]:
        try:
            return self._to_entity(MobileApp.objects.get(package_name=package_name))
        except MobileApp.DoesNotExist:
            return None


class DjangoUpdateRepository:
    """Fetches AppUpdate records from the database and maps them to domain entities.

    This class structurally implements UpdateRepository (Protocol).
    No inheritance needed — the method signatures satisfy the contract.
    """

    # ── Private helpers ──────────────────────────────────────────────────────

    def _to_entity(self, orm_obj: AppUpdate) -> AppUpdateEntity:
        return AppUpdateEntity(
            id=orm_obj.pk,
            app_id=orm_obj.app_id,
            version=orm_obj.version,
            apk_file_path=orm_obj.apk_file.name if orm_obj.apk_file else "",
            force_update=orm_obj.force_update,
            changelog=orm_obj.changelog,
            min_supported_version=orm_obj.min_supported_version,
            created_at=orm_obj.created_at,
        )

    # ── UpdateRepository Protocol ─────────────────────────────────────────────

    def get_latest(self, app_id: int) -> Optional[AppUpdateEntity]:
        """Return the most recent release for the given app, or None."""
        orm_obj = AppUpdate.objects.filter(app_id=app_id).first()
        return self._to_entity(orm_obj) if orm_obj else None

    def get_all(self, app_id: int) -> list[AppUpdateEntity]:
        """Return all releases for the given app, newest first."""
        return [self._to_entity(obj) for obj in AppUpdate.objects.filter(app_id=app_id)]


# Verify the concrete classes satisfy their Protocols at import time
assert isinstance(DjangoAppRepository(), AppRepository), (
    "DjangoAppRepository does not satisfy the AppRepository Protocol."
)
assert isinstance(DjangoUpdateRepository(), UpdateRepository), (
    "DjangoUpdateRepository does not satisfy the UpdateRepository Protocol. "
    "Check method signatures."
)
