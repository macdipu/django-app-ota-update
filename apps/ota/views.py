from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.ota.models import AppUpdate
from apps.ota.serializers import AppUpdateSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def latest_update(request):
    """Return the most recent APK release.

    GET /api/update/

    Response (200):
        {
            "version": "1.2.0",
            "apk_url": "https://yourdomain.com/media/apks/app.apk",
            "force_update": true,
            "changelog": "Bug fixes",
            "min_supported_version": "1.0.0",
            "created_at": "2024-01-01T00:00:00Z"
        }

    Response (404) when no releases exist:
        {"detail": "No updates available."}
    """
    update = AppUpdate.objects.first()  # ordering=-created_at is set on model Meta
    if update is None:
        return Response(
            {"detail": "No updates available."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = AppUpdateSerializer(update, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def update_history(request):
    """Return all APK releases, newest first.

    GET /api/updates/

    Response (200): list of AppUpdate objects (same shape as /api/update/)
    """
    updates = AppUpdate.objects.all()
    serializer = AppUpdateSerializer(updates, many=True, context={"request": request})
    return Response(serializer.data)
