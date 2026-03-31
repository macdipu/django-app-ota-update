import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class OtaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ota"
    verbose_name = "OTA Updates"

    def ready(self):
        """Import admin registrations and ensure the MinIO bucket exists."""
        import apps.ota.infrastructure.admin  # noqa: F401

        try:
            from django.core.files.storage import default_storage

            _ = default_storage
        except Exception:
            # Storage backend might not be ready in some contexts (e.g., migrate checks).
            logger.debug("Default storage backend not available during app ready.")

        # Create the media bucket if it does not exist yet.
        try:
            import boto3
            from botocore.exceptions import ClientError
            from django.conf import settings

            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            s3 = boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )

            try:
                s3.create_bucket(Bucket=bucket_name)
                logger.info("Created media bucket '%s'", bucket_name)
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code")
                if code in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                    logger.info("Media bucket '%s' already exists", bucket_name)
                else:
                    logger.warning("Could not ensure media bucket '%s': %s", bucket_name, exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to run MinIO bucket bootstrap: %s", exc)
