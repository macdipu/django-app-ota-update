from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core.health import health_check, db_health_check
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.ota.infrastructure.admin_site import ota_admin_site
from apps.ota.interfaces.ui import views as ui_views

urlpatterns = [
    # Root → Dashboard
    path("", lambda request: redirect("dashboard"), name="root"),
    path("dashboard/", ui_views.dashboard, name="dashboard"),
    path("dashboard/app/create/", ui_views.app_create, name="dashboard_app_create"),
    path("dashboard/app/<int:pk>/", ui_views.app_detail, name="dashboard_app_detail"),
    path("dashboard/app/<int:pk>/delete/", ui_views.app_delete, name="dashboard_app_delete"),
    path("dashboard/app/<int:app_pk>/release/<int:pk>/delete/", ui_views.release_delete, name="dashboard_release_delete"),

    path("admin/", ota_admin_site.urls),

    # OTA API
    path("api/", include("apps.ota.urls")),



    # Health checks
    path("health/", health_check, name="health"),
    path("health/db/", db_health_check, name="health-db"),

    # API schema & Swagger UI
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
