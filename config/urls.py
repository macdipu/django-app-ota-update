from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core.health import health_check, db_health_check
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.ota.admin_site import ota_admin_site

urlpatterns = [
    # Root → Swagger docs
    path("", lambda request: redirect("docs/"), name="root"),

    # Custom OTA admin site
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
