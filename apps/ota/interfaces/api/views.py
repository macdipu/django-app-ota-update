"""
Interfaces Layer — API Views (Controllers).

Thin HTTP adapters — responsibilities:
  1. Parse HTTP request (extract ?package query param)
  2. Call the appropriate use case via the DI factory
  3. Catch domain exceptions and map to HTTP status codes
  4. Serialize the result entity and return HTTP response

Views contain ZERO business logic. All decisions belong to use cases.

Dependency flow:
    View → di.build_*_use_case() → UseCase → Repository → Domain Entity
           ↑ only concrete reference is the DI factory
"""
from pathlib import Path

from django.http import FileResponse, Http404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.ota.domain.exceptions import AppNotFoundError, NoUpdatesAvailableError
from apps.ota.infrastructure.di import (
    build_latest_update_use_case,
    build_update_history_use_case,
)
from apps.ota.infrastructure.orm_models import AppUpdate
from apps.ota.interfaces.api.serializers import AppUpdateSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def latest_update(request):
    """Return the most recent APK release for the given app.

    GET /api/update/?package=com.example.merchant

    Query Params:
        package (str, required) — Android package name of the app.

    Responses:
        200 OK        — AppUpdateEntity JSON
        400 Bad Request — missing ?package param
        404 Not Found   — app not found, or app has no releases
    """
    package_name = request.query_params.get("package", "").strip()
    if not package_name:
        return Response(
            {"detail": "Missing required query parameter: 'package'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        entity = build_latest_update_use_case().execute(package_name=package_name)
    except (AppNotFoundError, NoUpdatesAvailableError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    serializer = AppUpdateSerializer(entity, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def update_history(request):
    """Return all APK releases for the given app, newest first.

    GET /api/updates/?package=com.example.merchant

    Query Params:
        package (str, required) — Android package name of the app.

    Responses:
        200 OK        — list of AppUpdateEntity JSON (empty list if no releases)
        400 Bad Request — missing ?package param
        404 Not Found   — app not found
    """
    package_name = request.query_params.get("package", "").strip()
    if not package_name:
        return Response(
            {"detail": "Missing required query parameter: 'package'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        entities = build_update_history_use_case().execute(package_name=package_name)
    except AppNotFoundError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    serializer = AppUpdateSerializer(entities, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def download_release(request, release_id: int):
    """Stream a private APK through Django so MinIO/S3 stays private."""

    try:
        release = AppUpdate.objects.get(pk=release_id)
    except AppUpdate.DoesNotExist as exc:
        raise Http404("Release not found.") from exc

    if not release.apk_file:
        raise Http404("APK file missing.")

    storage = release.apk_file.storage
    name = release.apk_file.name

    try:
        file_obj = storage.open(name, mode="rb")
    except FileNotFoundError as exc:
        raise Http404("APK file missing.") from exc
    except Exception as exc:  # pragma: no cover - backend-specific errors
        raise Http404("Unable to open APK file.") from exc

    response = FileResponse(
        file_obj,
        as_attachment=True,
        filename=Path(name).name,
        content_type="application/vnd.android.package-archive",
    )

    try:
        response["Content-Length"] = storage.size(name)
    except Exception:
        # Best-effort; size may not be available for streaming backends
        pass

    return response


