"""
Interfaces Layer — API Serializers.

Translates domain entities → JSON-serializable dicts.

Design notes:
  - Uses plain Serializer (not ModelSerializer) — decoupled from ORM.
  - ``apk_url`` is built HERE from entity.apk_file_path + MEDIA_URL.
    This is the correct boundary: the domain entity stores a storage-relative path;
    the interface layer resolves it to an absolute download URL for the client.
  - Requires serializer context to include the HTTP request for absolute URL building.

Usage in views:
    serializer = AppUpdateSerializer(entity, context={"request": request})
"""
from django.conf import settings
from django.urls import reverse
from apps.ota.infrastructure.storage import storage_service
from rest_framework import serializers


class AppUpdateSerializer(serializers.Serializer):
    """Serialize an AppUpdateEntity for HTTP response.

    Works for both a single entity and a list (many=True).
    """

    id = serializers.IntegerField(read_only=True)
    version = serializers.CharField(read_only=True)
    apk_url = serializers.SerializerMethodField()
    force_update = serializers.BooleanField(read_only=True)
    changelog = serializers.CharField(read_only=True)
    min_supported_version = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_apk_url(self, entity) -> str:
        """Build an absolute APK download URL from the entity's storage path.

        Resolution strategy:
          1. Use the storage backend to resolve the URL (supports S3/MinIO).
          2. If the storage URL is relative and a request is provided, build an
             absolute URL for clients.
          3. Fall back to MEDIA_URL + path for legacy behavior.
        """
        if not entity.apk_file_path:
            return ""

        request = self.context.get("request")

        if entity.id:
            download_path = reverse("ota-download", args=[entity.id])
            if request:
                return request.build_absolute_uri(download_path)
            return download_path

        try:
            return storage_service.url(entity.apk_file_path, request=request)
        except Exception:
            fallback = settings.MEDIA_URL.rstrip("/") + "/" + entity.apk_file_path
            return request.build_absolute_uri(fallback) if request else fallback
