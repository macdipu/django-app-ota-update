from django.apps import AppConfig


class OtaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ota"
    verbose_name = "OTA Updates"

    def ready(self):
        """Import infrastructure admin to register models with ota_admin_site."""
        import apps.ota.infrastructure.admin  # noqa: F401
        try:
            from django.core.files.storage import default_storage
            _ = default_storage
        except:
            pass
