"""
Use Case — Get Update History.

Orchestrates fetching all APK releases ordered newest-first.

Rule: This module may ONLY import from Python stdlib and apps.ota.domain.
"""
import logging

from apps.ota.domain.entities import AppUpdateEntity
from apps.ota.domain.repositories import UpdateRepository

logger = logging.getLogger(__name__)


class GetUpdateHistoryUseCase:
    """Return all AppUpdate records, newest first.

    Always succeeds — returns an empty list when no releases exist.
    """

    def __init__(self, repository: UpdateRepository) -> None:
        self._repository = repository

    def execute(self) -> list[AppUpdateEntity]:
        entities = self._repository.get_all()
        logger.debug("ota.use_case.get_history: returning %d releases", len(entities))
        return entities
