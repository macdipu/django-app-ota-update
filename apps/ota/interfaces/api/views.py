"""
Interfaces Layer — API Views (Controllers).

Thin HTTP adapters — responsibilities:
  1. Parse HTTP request
  2. Call the appropriate use case via the DI factory
  3. Catch domain exceptions and map to HTTP status codes
  4. Serialize the result entity and return HTTP response

Views contain ZERO business logic. All decisions belong to use cases.

Dependency flow:
    View → di.build_*_use_case() → UseCase → Repository → Domain Entity
           ↑ only concrete reference is the DI factory
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.ota.domain.exceptions import NoUpdatesAvailableError
from apps.ota.infrastructure.di import (
    build_latest_update_use_case,
    build_update_history_use_case,
)
from apps.ota.interfaces.api.serializers import AppUpdateSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def latest_update(request):
    """Return the most recent APK release.

    GET /api/update/

    Responses:
        200 OK  — AppUpdateEntity JSON
        404 Not Found — {"detail": "..."}  when no releases exist
    """
    try:
        entity = build_latest_update_use_case().execute()
    except NoUpdatesAvailableError as exc:
        # Domain exception → HTTP 404 (mapping done HERE, not in use case)
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    serializer = AppUpdateSerializer(entity, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def update_history(request):
    """Return all APK releases, newest first.

    GET /api/updates/

    Responses:
        200 OK — list of AppUpdateEntity JSON (empty list if no releases)
    """
    entities = build_update_history_use_case().execute()
    serializer = AppUpdateSerializer(entities, many=True, context={"request": request})
    return Response(serializer.data)
