"""
Domain Layer — Business Exceptions.

Domain exceptions communicate business rule violations.
They carry NO HTTP status codes — that mapping is the interface layer's job.

Rule: This module may ONLY import from Python stdlib.
"""


class OtaDomainError(Exception):
    """Base class for all OTA domain errors."""


class NoUpdatesAvailableError(OtaDomainError):
    """Raised when no APK releases have been published yet.

    The interface layer maps this to HTTP 404.
    Use cases raise this instead of returning None to make the failure
    explicit, typed, and testable without inspecting return values.
    """

    def __init__(self, message: str = "No APK releases have been published yet."):
        super().__init__(message)


class InvalidVersionError(OtaDomainError):
    """Raised when a version string does not meet domain constraints."""
