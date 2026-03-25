"""
Domain Layer — Repository Contract (Port).

Defined as a typing.Protocol so implementors need NOT inherit from this class.
Any class with matching method signatures automatically satisfies the contract
(structural subtyping). This is mypy/pyright-compatible and avoids coupling
infrastructure to the domain through inheritance.

Rule: This module may ONLY import from Python stdlib and apps.ota.domain.
"""
from typing import Optional, Protocol, runtime_checkable

from apps.ota.domain.entities import AppUpdateEntity


@runtime_checkable
class UpdateRepository(Protocol):
    """Port — data-access contract that use cases depend on.

    Concrete implementations live in infrastructure/repositories.py.
    Test doubles (fakes) live in test/.
    """

    def get_latest(self) -> Optional[AppUpdateEntity]:
        """Return the most recent update entity, or None if no releases exist."""
        ...

    def get_all(self) -> list[AppUpdateEntity]:
        """Return all release entities ordered newest-first."""
        ...
