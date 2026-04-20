from django.db import connection
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"})


def db_health_check(request):
    try:
        connection.ensure_connection()
        return JsonResponse({"database": "ok"})
    except Exception:
        return JsonResponse({"database": "error"}, status=500)
