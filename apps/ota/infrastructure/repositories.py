"""
Infrastructure Layer — Concrete Django ORM Repository.

Implements the UpdateRepository Protocol from the domain layer.
Translates ORM model instances → domain entities.

Design note on apk_file_path:
    The repository stores only the storage-relative path (orm_obj.apk_file.name).
    It does NOT resolve HTTP URLs — that is a presentation concern handled
    at the interface/serializer boundary.

Rule: May import from domain layer and Django ORM only.
"""
from typing import Optional

from apps.ota.domain.entities import AppUpdateEntity
from apps.ota.domain.repositories import UpdateRepository  # Protocol — for type hints
from apps.ota.infrastructure.orm_models import AppUpdate


class DjangoUpdateRepository:
    """Fetches AppUpdate records from the database and maps them to domain entities.

    This class structurally implements UpdateRepository (Protocol).
    No inheritance needed — the method signatures satisfy the contract.
    """

    # ── Private helpers ──────────────────────────────────────────────────────

    def _to_entity(self, orm_obj: AppUpdate) -> AppUpdateEntity:
        return AppUpdateEntity(
            id=orm_obj.pk,
            version=orm_obj.version,
            apk_file_path=orm_obj.apk_file.name if orm_obj.apk_file else "",
            force_update=orm_obj.force_update,
            changelog=orm_obj.changelog,
            min_supported_version=orm_obj.min_supported_version,
            created_at=orm_obj.created_at,
        )

    # ── UpdateRepository Protocol ─────────────────────────────────────────────

    def get_latest(self) -> Optional[AppUpdateEntity]:
        """Return the most recent release or None."""
        orm_obj = AppUpdate.objects.first()  # Meta.ordering = ['-created_at']
        return self._to_entity(orm_obj) if orm_obj else None

    def get_all(self) -> list[AppUpdateEntity]:
        """Return all releases, newest first."""
        return [self._to_entity(obj) for obj in AppUpdate.objects.all()]


# Verify the concrete class satisfies the Protocol at import time (runtime check)
assert isinstance(DjangoUpdateRepository(), UpdateRepository), (
    "DjangoUpdateRepository does not satisfy the UpdateRepository Protocol. "
    "Check method signatures."
)
