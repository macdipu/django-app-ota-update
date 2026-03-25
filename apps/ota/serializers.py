from rest_framework import serializers

from apps.ota.models import AppUpdate


class AppUpdateSerializer(serializers.ModelSerializer):
    """Serializes AppUpdate records for the public API.

    Replaces ``apk_file`` with a full absolute ``apk_url`` so the Flutter
    client can download the APK directly without knowing the server's base URL.
    """

    apk_url = serializers.SerializerMethodField()

    class Meta:
        model = AppUpdate
        fields = [
            "version",
            "apk_url",
            "force_update",
            "changelog",
            "min_supported_version",
            "created_at",
        ]

    def get_apk_url(self, obj) -> str:
        request = self.context.get("request")
        if request and obj.apk_file:
            return request.build_absolute_uri(obj.apk_file.url)
        return obj.apk_file.url if obj.apk_file else ""
