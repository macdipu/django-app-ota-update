"""
Infrastructure Layer — Custom Django AdminSite.

Moved here (Δ8) from the package root since it's a framework concern.
The custom AdminSite handles:
  - Custom branding (header, title)
  - "Remember Me" login (30-day session extension)
"""
from django.contrib.admin import AdminSite


class OtaAdminSite(AdminSite):
    """Custom admin site for OTA Update Manager with remember-me login."""

    site_header = "OTA Update Manager"
    site_title = "OTA Admin"
    index_title = "Dashboard"
    site_url = None  # Remove "View Site" link from header
    login_template = "dashboard/login.html"

    def login(self, request, extra_context=None):
        """Override login to support 'Remember Me' checkbox.

        If checked: session lasts 30 days.
        If unchecked: session expires when the browser closes.
        """
        response = super().login(request, extra_context=extra_context)

        if request.method == "POST" and request.user.is_authenticated:
            if request.POST.get("remember_me"):
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 days
            else:
                request.session.set_expiry(0)  # Expire on browser close

        return response

    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        from apps.ota.interfaces.ui import views as ui_views
        
        custom_urls = [
            path("app/create/", self.admin_view(ui_views.app_create), name="ui_app_create"),
            path("app/<int:pk>/", self.admin_view(ui_views.app_detail), name="ui_app_detail"),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        from apps.ota.interfaces.ui.views import dashboard
        return dashboard(request)


# Singleton — imported by infrastructure/admin.py and config/urls.py
ota_admin_site = OtaAdminSite(name="ota_admin")
