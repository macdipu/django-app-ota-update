"""
Infrastructure Layer — Django Admin registration.

Registers MobileApp and AppUpdate ORM models with the custom OtaAdminSite.
Features:
  - MobileApp changelist with icon, release count, latest version badge
  - AppUpdate inline inside MobileApp detail page
  - Drag-and-drop APK upload on the AppUpdate add/change form
"""
import os
from django.core.exceptions import SuspiciousFileOperation

from django.contrib import admin as default_admin
from django.utils.html import format_html

from apps.ota.infrastructure.admin_site import ota_admin_site
from apps.ota.infrastructure.orm_models import AppUpdate, MobileApp
from apps.ota.infrastructure.storage import storage_service


# ── Inline: App Releases inside MobileApp ───────────────────────────────────

class AppUpdateInline(default_admin.TabularInline):
    model = AppUpdate
    extra = 0
    fields = ("version", "build_number", "force_update", "apk_file", "created_at")
    readonly_fields = ("created_at", "build_number")
    show_change_link = True
    can_delete = True
    ordering = ("-created_at",)


# ── MobileApp Admin ──────────────────────────────────────────────────────────

@default_admin.register(MobileApp, site=ota_admin_site)
class MobileAppAdmin(default_admin.ModelAdmin):
    list_display = ("app_icon_display", "name", "package_name", "release_count_badge", "latest_version_badge", "created_at")
    search_fields = ("name", "package_name")
    ordering = ("name",)
    readonly_fields = ("created_at", "app_icon_preview")
    inlines = [AppUpdateInline]

    fieldsets = (
        (
            "App Info",
            {"fields": ("name", "package_name", "description")},
        ),
        (
            "Icon",
            {"fields": ("icon", "app_icon_preview"), "classes": ("wide",)},
        ),
        (
            "Metadata",
            {"fields": ("created_at",), "classes": ("collapse",)},
        ),
    )

    @default_admin.display(description="")
    def app_icon_display(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:8px;object-fit:cover;" />',
                obj.icon.url,
            )
        initials = (obj.name[:2] if obj.name else "??").upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#7c3aed,#06b6d4);'
            'display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:white;">{}</div>',
            initials,
        )

    @default_admin.display(description="App Icon")
    def app_icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" style="width:80px;height:80px;border-radius:14px;object-fit:cover;" />',
                obj.icon.url,
            )
        return "—"

    @default_admin.display(description="Releases")
    def release_count_badge(self, obj):
        count = obj.release_count
        color = "#7c3aed"
        return format_html(
            '<span style="background:{}22;color:{};border:1px solid {}55;padding:3px 10px;'
            'border-radius:20px;font-size:12px;font-weight:600;">{}</span>',
            color, color, color, count,
        )

    @default_admin.display(description="Latest Version")
    def latest_version_badge(self, obj):
        version = obj.latest_version
        if version == "—":
            return format_html(
                '<span style="color:#475569;font-size:12px;">No releases</span>'
            )
        return format_html(
            '<span style="background:#06b6d422;color:#06b6d4;border:1px solid #06b6d455;padding:3px 10px;'
            'border-radius:20px;font-size:12px;font-weight:600;">{}</span>',
            f"v{version}",
        )


# ── AppUpdate Admin ──────────────────────────────────────────────────────────

@default_admin.register(AppUpdate, site=ota_admin_site)
class AppUpdateAdmin(default_admin.ModelAdmin):
    list_display = ("version_badge", "build_number", "app_link", "force_update_display", "min_supported_version", "apk_download_link", "created_at")
    list_filter = ("force_update", "app")
    search_fields = ("version", "changelog", "app__name", "app__package_name")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "apk_download_link", "build_number")
    autocomplete_fields = []

    fieldsets = (
        (
            "App & Release Info",
            {"fields": ("app", "version", "build_number", "force_update", "min_supported_version")},
        ),
        (
            "APK File",
            {"fields": ("apk_file",), "classes": ("wide",)},
        ),
        (
            "Changelog",
            {"fields": ("changelog",), "classes": ("wide",)},
        ),
        (
            "Metadata",
            {"fields": ("created_at", "apk_download_link"), "classes": ("collapse",)},
        ),
    )

    class Media:
        # Custom drag-and-drop JS loaded on the change form
        js = ("admin/js/apk_dropzone.js",)
        css = {"all": ("admin/css/apk_dropzone.css",)}

    @default_admin.display(description="Version")
    def version_badge(self, obj):
        return format_html(
            '<span style="background:#7c3aed22;color:#7c3aed;border:1px solid #7c3aed55;padding:3px 10px;'
            'border-radius:20px;font-size:12px;font-weight:700;">v{}</span>',
            obj.version,
        )

    @default_admin.display(description="App")
    def app_link(self, obj):
        return format_html(
            '<a href="/admin/ota/mobileapp/{}/change/" style="color:#06b6d4;font-weight:500;">{}</a>',
            obj.app_id,
            obj.app.name,
        )

    @default_admin.display(description="Force Update", boolean=True)
    def force_update_display(self, obj):
        return obj.force_update

    @default_admin.display(description="Download APK")
    def apk_download_link(self, obj):
        if obj.apk_file:
            size_str = ""
            try:
                size_mb = obj.apk_file.size / (1024 * 1024)
                size_str = f" ({size_mb:.1f} MB)" if size_mb else ""
            except (FileNotFoundError, SuspiciousFileOperation, OSError):
                # Size lookup can fail on remote storage or missing files; skip display in that case.
                size_str = ""
            try:
                download_url = storage_service.url(obj.apk_file.name)
            except Exception:
                download_url = obj.apk_file.url
            return format_html(
                '<a href="{}" target="_blank" download style="color:#06b6d4;font-weight:500;">⬇ Download{}</a>',
                download_url,
                size_str,
            )
        return "—"
