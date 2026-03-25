"""
Infrastructure Layer — Dependency Injection Factory (DI Container).

Single place to wire use cases to their concrete implementations.
Views import from here — they never reference concrete repository classes directly.

To swap implementations (e.g. cache-backed, S3-backed), change only this file.

Usage:
    from apps.ota.infrastructure.di import build_latest_update_use_case

    use_case = build_latest_update_use_case()
    entity = use_case.execute()
"""
from apps.ota.domain.repositories import UpdateRepository
from apps.ota.infrastructure.repositories import DjangoUpdateRepository
from apps.ota.use_cases.get_latest_update import GetLatestUpdateUseCase
from apps.ota.use_cases.get_update_history import GetUpdateHistoryUseCase


def _get_repository() -> UpdateRepository:
    """Return the active repository implementation.

    Swap this single line to change the storage backend project-wide.
    """
    return DjangoUpdateRepository()


def build_latest_update_use_case() -> GetLatestUpdateUseCase:
    """Construct GetLatestUpdateUseCase with its concrete dependency."""
    return GetLatestUpdateUseCase(repository=_get_repository())


def build_update_history_use_case() -> GetUpdateHistoryUseCase:
    """Construct GetUpdateHistoryUseCase with its concrete dependency."""
    return GetUpdateHistoryUseCase(repository=_get_repository())
