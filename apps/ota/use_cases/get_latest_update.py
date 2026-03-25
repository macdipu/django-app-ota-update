"""
Use Case — Get Latest Update.

Orchestrates fetching the single most recent APK release.

Dependencies (injected):
    repository: UpdateRepository  ← domain port (Protocol)

Raises:
    NoUpdatesAvailableError  ← domain exception; interface layer maps to HTTP 404

Rule: This module may ONLY import from Python stdlib and apps.ota.domain.
"""
import logging
from typing import Optional

from apps.ota.domain.entities import AppUpdateEntity
from apps.ota.domain.exceptions import NoUpdatesAvailableError
from apps.ota.domain.repositories import UpdateRepository

logger = logging.getLogger(__name__)


class GetLatestUpdateUseCase:
    """Return the most recent AppUpdate or raise NoUpdatesAvailableError.

    Design note: raises instead of returning Optional so the interface layer
    doesn't need to understand what None means in business terms.
    """

    def __init__(self, repository: UpdateRepository) -> None:
        self._repository = repository

    def execute(self) -> AppUpdateEntity:
        entity = self._repository.get_latest()

        if entity is None:
            logger.info("ota.use_case.get_latest: no releases available")
            raise NoUpdatesAvailableError()

        logger.info(
            "ota.use_case.get_latest: serving version=%s force_update=%s",
            entity.version,
            entity.force_update,
        )
        return entity
