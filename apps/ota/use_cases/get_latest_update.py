"""
Use Case — Get Latest Update.

Orchestrates fetching the single most recent APK release for a given app.

Dependencies (injected):
    app_repository:    AppRepository  ← resolves package_name → app_id
    update_repository: UpdateRepository  ← fetches releases

Raises:
    AppNotFoundError         ← when package_name doesn't match any app
    NoUpdatesAvailableError  ← when app has no releases

Rule: This module may ONLY import from Python stdlib and apps.ota.domain.
"""
import logging

from apps.ota.domain.entities import AppUpdateEntity
from apps.ota.domain.exceptions import NoUpdatesAvailableError, AppNotFoundError
from apps.ota.domain.repositories import AppRepository, UpdateRepository

logger = logging.getLogger(__name__)


class GetLatestUpdateUseCase:
    """Return the most recent AppUpdate for the given app or raise a domain error.

    Design note: raises instead of returning Optional so the interface layer
    doesn't need to understand what None means in business terms.
    """

    def __init__(self, app_repository: AppRepository, update_repository: UpdateRepository) -> None:
        self._app_repo = app_repository
        self._update_repo = update_repository

    def execute(self, package_name: str) -> AppUpdateEntity:
        app = self._app_repo.get_app_by_package(package_name)
        if app is None:
            logger.info("ota.use_case.get_latest: app not found package=%s", package_name)
            raise AppNotFoundError(package_name)

        entity = self._update_repo.get_latest(app.id)
        if entity is None:
            logger.info("ota.use_case.get_latest: no releases for package=%s", package_name)
            raise NoUpdatesAvailableError()

        logger.info(
            "ota.use_case.get_latest: serving package=%s version=%s force_update=%s",
            package_name,
            entity.version,
            entity.force_update,
        )
        return entity
