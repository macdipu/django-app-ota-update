"""
Pure Use Case Unit Tests — Clean Architecture Reference Implementation.

These tests exercise ONLY the use case and domain layers.
They use fake repositories.
"""
from datetime import datetime, timezone
from unittest import TestCase

from apps.ota.domain.entities import AppUpdateEntity, MobileAppEntity
from apps.ota.domain.exceptions import NoUpdatesAvailableError, AppNotFoundError
from apps.ota.use_cases.get_latest_update import GetLatestUpdateUseCase
from apps.ota.use_cases.get_update_history import GetUpdateHistoryUseCase


# ── Test Doubles ──────────────────────────────────────────────────────────────

class InMemoryAppRepository:
    def __init__(self, apps=None):
        self._apps = apps or []

    def get_all_apps(self):
        return self._apps
        
    def get_app_by_package(self, package_name: str):
        for app in self._apps:
            if app.package_name == package_name:
                return app
        return None

class InMemoryUpdateRepository:
    def __init__(self, items=None):
        self._items = items or []

    def get_latest(self, app_id: int):
        filtered = [i for i in self._items if i.app_id == app_id]
        return filtered[0] if filtered else None

    def get_all(self, app_id: int):
        return [i for i in self._items if i.app_id == app_id]


def _make_app(**kwargs) -> MobileAppEntity:
    defaults = dict(id=1, name="App", package_name="com.test.app", description="", created_at=datetime.now(timezone.utc))
    defaults.update(kwargs)
    return MobileAppEntity(**defaults)

def _make_entity(**kwargs) -> AppUpdateEntity:
    defaults = dict(
        id=1,
        app_id=1,
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
    def setUp(self):
        self.app = _make_app(id=1, package_name="com.test.app")
        self.app_repo = InMemoryAppRepository(apps=[self.app])

    def test_raises_app_not_found_error(self):
        use_case = GetLatestUpdateUseCase(app_repository=self.app_repo, update_repository=InMemoryUpdateRepository())
        with self.assertRaises(AppNotFoundError):
            use_case.execute("com.unknown")

    def test_raises_no_updates_when_repository_is_empty(self):
        use_case = GetLatestUpdateUseCase(app_repository=self.app_repo, update_repository=InMemoryUpdateRepository())
        with self.assertRaises(NoUpdatesAvailableError):
            use_case.execute("com.test.app")

    def test_returns_single_entity(self):
        entity = _make_entity(app_id=1, version="1.0.0")
        update_repo = InMemoryUpdateRepository(items=[entity])
        use_case = GetLatestUpdateUseCase(app_repository=self.app_repo, update_repository=update_repo)
        
        result = use_case.execute("com.test.app")
        self.assertEqual(result.version, "1.0.0")


# ── GetUpdateHistoryUseCase ───────────────────────────────────────────────────

class TestGetUpdateHistoryUseCase(TestCase):
    def setUp(self):
        self.app = _make_app(id=1, package_name="com.test.app")
        self.app_repo = InMemoryAppRepository(apps=[self.app])

    def test_raises_app_not_found(self):
        use_case = GetUpdateHistoryUseCase(app_repository=self.app_repo, update_repository=InMemoryUpdateRepository())
        with self.assertRaises(AppNotFoundError):
            use_case.execute("com.unknown")

    def test_returns_empty_list_when_no_releases(self):
        use_case = GetUpdateHistoryUseCase(app_repository=self.app_repo, update_repository=InMemoryUpdateRepository())
        result = use_case.execute("com.test.app")
        self.assertEqual(result, [])

    def test_returns_filtered_entities(self):
        entities = [
            _make_entity(id=1, app_id=1, version="1.0.0"),
            _make_entity(id=2, app_id=2, version="X.Y.Z"), # Different app
            _make_entity(id=3, app_id=1, version="2.0.0"),
        ]
        update_repo = InMemoryUpdateRepository(items=entities)
        use_case = GetUpdateHistoryUseCase(app_repository=self.app_repo, update_repository=update_repo)

        result = use_case.execute("com.test.app")
        self.assertEqual(len(result), 2)
        versions = [e.version for e in result]
        self.assertIn("1.0.0", versions)
        self.assertIn("2.0.0", versions)
