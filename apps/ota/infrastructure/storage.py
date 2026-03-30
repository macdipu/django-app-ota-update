"""
Storage service adapter to keep storage logic in one place.

Uses Django's default_storage so it works with FileSystem, S3/MinIO, etc.
Provides URL resolution that can return presigned URLs when supported by
the backend (e.g., S3Boto3Storage with private buckets).
"""
from typing import Optional

from django.core.files.storage import Storage, default_storage


class StorageService:
    def __init__(self, storage: Storage = default_storage):
        self._storage = storage

    def url(self, name: str, request=None) -> str:
        """Return a URL for the stored object, preserving presigned semantics.

        If the storage returns a relative URL and a request is provided, build
        an absolute URL for client consumption.
        """
        url = self._storage.url(name)
        if request and url.startswith("/"):
            return request.build_absolute_uri(url)
        return url

    def delete(self, name: str) -> None:
        self._storage.delete(name)

    def size(self, name: str) -> int:
        return self._storage.size(name)


storage_service = StorageService()

