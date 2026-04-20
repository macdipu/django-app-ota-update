"""
Use Case — Get Update History.

Orchestrates fetching all APK releases for a given app, ordered newest-first.

Rule: This module may ONLY import from Python stdlib and apps.ota.domain.
"""
import logging

from apps.ota.domain.entities import AppUpdateEntity
from apps.ota.domain.exceptions import AppNotFoundError
from apps.ota.domain.repositories import AppRepository, UpdateRepository

logger = logging.getLogger(__name__)


class GetUpdateHistoryUseCase:
    """Return all AppUpdate records for the given app, newest first.

    Always succeeds — returns an empty list when no releases exist.
    Raises AppNotFoundError if package_name is unknown.
    """

    def __init__(self, app_repository: AppRepository, update_repository: UpdateRepository) -> None:
        self._app_repo = app_repository
        self._update_repo = update_repository

    def execute(self, package_name: str) -> list[AppUpdateEntity]:
        app = self._app_repo.get_app_by_package(package_name)
        if app is None:
            raise AppNotFoundError(package_name)

        entities = self._update_repo.get_all(app.id)
        logger.debug(
            "ota.use_case.get_history: returning %d releases for package=%s",
            len(entities),
            package_name,
        )
        return entities
