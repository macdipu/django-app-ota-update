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


class AppNotFoundError(OtaDomainError):
    """Raised when the requested package_name does not match any registered app.

    The interface layer maps this to HTTP 404.
    """

    def __init__(self, package_name: str = ""):
        msg = f"No app found with package name '{package_name}'." if package_name else "App not found."
        super().__init__(msg)


class InvalidVersionError(OtaDomainError):
    """Raised when a version string does not meet domain constraints."""
