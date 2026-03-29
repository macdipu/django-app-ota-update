"""
Infrastructure Layer — Dependency Injection Factory (DI Container).

Single place to wire use cases to their concrete implementations.
Views import from here — they never reference concrete repository classes directly.

To swap implementations (e.g. cache-backed, S3-backed), change only this file.

Usage:
    from apps.ota.infrastructure.di import build_latest_update_use_case

    use_case = build_latest_update_use_case()
    entity = use_case.execute(package_name="com.example.merchant")
"""
from apps.ota.infrastructure.repositories import DjangoAppRepository, DjangoUpdateRepository
from apps.ota.use_cases.get_latest_update import GetLatestUpdateUseCase
from apps.ota.use_cases.get_update_history import GetUpdateHistoryUseCase


def _get_app_repository() -> DjangoAppRepository:
    return DjangoAppRepository()


def _get_update_repository() -> DjangoUpdateRepository:
    return DjangoUpdateRepository()


def build_latest_update_use_case() -> GetLatestUpdateUseCase:
    """Construct GetLatestUpdateUseCase with its concrete dependencies."""
    return GetLatestUpdateUseCase(
        app_repository=_get_app_repository(),
        update_repository=_get_update_repository(),
    )


def build_update_history_use_case() -> GetUpdateHistoryUseCase:
    """Construct GetUpdateHistoryUseCase with its concrete dependencies."""
    return GetUpdateHistoryUseCase(
        app_repository=_get_app_repository(),
        update_repository=_get_update_repository(),
    )
