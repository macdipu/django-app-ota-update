"""
Pure Use Case Unit Tests — Clean Architecture Reference Implementation.

Key Design Principle
--------------------
These tests exercise ONLY the use case and domain layers.
They use an InMemoryUpdateRepository (a test double / fake) — no database,
no Django, no HTTP. Tests run in microseconds.

This is the biggest practical benefit of Clean Architecture: business logic
can be verified instantly without framework overhead.

Test Double Types Used Here
---------------------------
Fake    — InMemoryUpdateRepository: real working implementation in memory.
          Preferred over mocks because it's simpler and less fragile.

Structure mirrors the use case structure:
  test_use_cases.py
  ├── InMemoryUpdateRepository      ← shared fake
  ├── TestGetLatestUpdateUseCase    ← unit tests for GetLatestUpdateUseCase
  └── TestGetUpdateHistoryUseCase   ← unit tests for GetUpdateHistoryUseCase
"""
from datetime import datetime, timezone
from unittest import TestCase

import pytest

from apps.ota.domain.entities import AppUpdateEntity
from apps.ota.domain.exceptions import NoUpdatesAvailableError
from apps.ota.use_cases.get_latest_update import GetLatestUpdateUseCase
from apps.ota.use_cases.get_update_history import GetUpdateHistoryUseCase


# ── Test Double ───────────────────────────────────────────────────────────────

class InMemoryUpdateRepository:
    """Fake repository satisfying the UpdateRepository Protocol.

    No database, no ORM. Used only in tests.
    Items are stored in the order they are given — index 0 is treated as 'latest'
    (mirrors Meta.ordering = ['-created_at'] in the real ORM model).
    """

    def __init__(self, items: list[AppUpdateEntity] | None = None) -> None:
        self._items = items or []

    def get_latest(self) -> AppUpdateEntity | None:
        return self._items[0] if self._items else None

    def get_all(self) -> list[AppUpdateEntity]:
        return list(self._items)


def _make_entity(**kwargs) -> AppUpdateEntity:
    """Factory: create a minimal valid AppUpdateEntity with sensible defaults."""
    defaults = dict(
        id=1,
        version="1.0.0",
        apk_file_path="apks/app-v1.0.0.apk",
        force_update=False,
        changelog="",
        min_supported_version="",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return AppUpdateEntity(**defaults)


# ── GetLatestUpdateUseCase ────────────────────────────────────────────────────

class TestGetLatestUpdateUseCase(TestCase):
    """Unit tests for GetLatestUpdateUseCase.

    All tests use InMemoryUpdateRepository — zero DB, zero HTTP.
    """

    def test_raises_no_updates_when_repository_is_empty(self):
        """Must raise NoUpdatesAvailableError when no releases exist."""
        repo = InMemoryUpdateRepository(items=[])
        use_case = GetLatestUpdateUseCase(repository=repo)

        with self.assertRaises(NoUpdatesAvailableError):
            use_case.execute()

    def test_returns_single_entity(self):
        """Returns the only entity when exactly one release exists."""
        entity = _make_entity(version="1.0.0")
        repo = InMemoryUpdateRepository(items=[entity])

        result = GetLatestUpdateUseCase(repository=repo).execute()

        self.assertEqual(result.version, "1.0.0")

    def test_returns_first_item_as_latest(self):
        """First item (index 0) is treated as the latest release."""
        older = _make_entity(id=1, version="1.0.0")
        newer = _make_entity(id=2, version="2.0.0")
        repo = InMemoryUpdateRepository(items=[newer, older])

        result = GetLatestUpdateUseCase(repository=repo).execute()

        self.assertEqual(result.version, "2.0.0")

    def test_entity_fields_are_passed_through_unchanged(self):
        """All entity fields must survive the use case without mutation."""
        entity = _make_entity(
            version="3.0.0",
            apk_file_path="apks/app-v3.0.0.apk",
            force_update=True,
            changelog="Major release",
            min_supported_version="2.0.0",
        )
        repo = InMemoryUpdateRepository(items=[entity])

        result = GetLatestUpdateUseCase(repository=repo).execute()

        self.assertEqual(result.apk_file_path, "apks/app-v3.0.0.apk")
        self.assertTrue(result.force_update)
        self.assertEqual(result.changelog, "Major release")
        self.assertEqual(result.min_supported_version, "2.0.0")

    def test_no_updates_error_message_is_meaningful(self):
        """The error message must be non-empty and user-readable."""
        repo = InMemoryUpdateRepository()
        use_case = GetLatestUpdateUseCase(repository=repo)

        with self.assertRaises(NoUpdatesAvailableError) as ctx:
            use_case.execute()

        self.assertGreater(len(str(ctx.exception)), 10)

    def test_protocol_compliance_of_fake(self):
        """InMemoryUpdateRepository must structurally satisfy UpdateRepository Protocol."""
        from apps.ota.domain.repositories import UpdateRepository
        repo = InMemoryUpdateRepository()
        self.assertIsInstance(repo, UpdateRepository)


# ── GetUpdateHistoryUseCase ───────────────────────────────────────────────────

class TestGetUpdateHistoryUseCase(TestCase):
    """Unit tests for GetUpdateHistoryUseCase."""

    def test_returns_empty_list_when_no_releases(self):
        """Must return an empty list (not raise) when DB is empty."""
        repo = InMemoryUpdateRepository(items=[])

        result = GetUpdateHistoryUseCase(repository=repo).execute()

        self.assertEqual(result, [])

    def test_returns_all_entities(self):
        """Must return all entities from the repository."""
        entities = [
            _make_entity(id=1, version="1.0.0"),
            _make_entity(id=2, version="2.0.0"),
            _make_entity(id=3, version="3.0.0"),
        ]
        repo = InMemoryUpdateRepository(items=entities)

        result = GetUpdateHistoryUseCase(repository=repo).execute()

        self.assertEqual(len(result), 3)
        versions = [e.version for e in result]
        self.assertIn("1.0.0", versions)
        self.assertIn("3.0.0", versions)

    def test_order_is_preserved_from_repository(self):
        """Use case must NOT reorder results — ordering is the repository's responsibility."""
        entities = [
            _make_entity(id=2, version="2.0.0"),
            _make_entity(id=1, version="1.0.0"),
        ]
        repo = InMemoryUpdateRepository(items=entities)

        result = GetUpdateHistoryUseCase(repository=repo).execute()

        self.assertEqual(result[0].version, "2.0.0")
        self.assertEqual(result[1].version, "1.0.0")
