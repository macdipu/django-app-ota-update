from django.urls import path

from apps.ota.interfaces.api import views

urlpatterns = [
    # GET /api/update/   → latest release
    path("update/", views.latest_update, name="ota-latest"),
    # GET /api/updates/  → full release history
    path("updates/", views.update_history, name="ota-history"),
    # GET /api/download/<id>/ → proxy an APK download through Django
    path("download/<int:release_id>/", views.download_release, name="ota-download"),
]
