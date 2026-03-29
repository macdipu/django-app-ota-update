"""
Domain Layer — Repository Contracts (Ports).

Defined as typing.Protocol so implementors need NOT inherit from this class.
Any class with matching method signatures automatically satisfies the contract
(structural subtyping). This is mypy/pyright-compatible and avoids coupling
infrastructure to the domain through inheritance.

Rule: This module may ONLY import from Python stdlib and apps.ota.domain.
"""
from typing import Optional, Protocol, runtime_checkable

from apps.ota.domain.entities import AppUpdateEntity, MobileAppEntity


@runtime_checkable
class AppRepository(Protocol):
    """Port — contract for fetching registered mobile apps."""

    def get_all_apps(self) -> list[MobileAppEntity]:
        """Return all registered mobile apps."""
        ...

    def get_app_by_package(self, package_name: str) -> Optional[MobileAppEntity]:
        """Return a MobileApp by package name, or None if not found."""
        ...


@runtime_checkable
class UpdateRepository(Protocol):
    """Port — data-access contract that use cases depend on.

    Concrete implementations live in infrastructure/repositories.py.
    Test doubles (fakes) live in test/.
    """

    def get_latest(self, app_id: int) -> Optional[AppUpdateEntity]:
        """Return the most recent update entity for the given app, or None."""
        ...

    def get_all(self, app_id: int) -> list[AppUpdateEntity]:
        """Return all release entities for the given app, ordered newest-first."""
        ...
