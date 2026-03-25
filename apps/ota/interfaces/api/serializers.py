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
from rest_framework import serializers


class AppUpdateSerializer(serializers.Serializer):
    """Serialize an AppUpdateEntity for HTTP response.

    Works for both a single entity and a list (many=True).
    """

    version = serializers.CharField(read_only=True)
    apk_url = serializers.SerializerMethodField()
    force_update = serializers.BooleanField(read_only=True)
    changelog = serializers.CharField(read_only=True)
    min_supported_version = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_apk_url(self, entity) -> str:
        """Build an absolute APK download URL from the entity's storage path.

        Resolution strategy:
          1. Use request.build_absolute_uri() if the request is in context
             (preferred — correct even behind a reverse proxy).
          2. Fall back to MEDIA_URL + path (useful in management commands/tests).
          3. Return raw path if no MEDIA_URL configured.
        """
        if not entity.apk_file_path:
            return ""

        relative_url = settings.MEDIA_URL.rstrip("/") + "/" + entity.apk_file_path

        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(relative_url)

        return relative_url
