from django.contrib import admin as default_admin
from django.utils.html import format_html

from apps.ota.admin_site import ota_admin_site
from apps.ota.models import AppUpdate


@ota_admin_site.register(AppUpdate)
class AppUpdateAdmin(default_admin.ModelAdmin):
    list_display = ("version", "force_update", "min_supported_version", "apk_download_link", "created_at")
    list_filter = ("force_update",)
    search_fields = ("version", "changelog")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "apk_download_link")

    fieldsets = (
        (
            "Release Info",
            {
                "fields": ("version", "apk_file", "force_update", "min_supported_version"),
            },
        ),
        (
            "Changelog",
            {
                "fields": ("changelog",),
                "classes": ("wide",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "apk_download_link"),
                "classes": ("collapse",),
            },
        ),
    )

    @default_admin.display(description="Download APK")
    def apk_download_link(self, obj):
        if obj.apk_file:
            return format_html(
                '<a href="{}" target="_blank" download>⬇ Download</a>',
                obj.apk_file.url,
            )
        return "—"
