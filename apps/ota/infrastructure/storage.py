"""
Storage service adapter to keep storage logic in one place.

Uses Django's default_storage so it works with FileSystem, S3/MinIO, etc.
Provides URL resolution that can return presigned URLs when supported by
the storage backend (e.g., S3Boto3Storage with private buckets).
Supports an optional MEDIA_PUBLIC_BASE_URL override when the storage
endpoint host is not directly reachable by browsers (e.g., docker service names).
"""
from urllib.parse import urlparse, urlunparse
import json

from django.conf import settings
from django.core.files.storage import Storage, default_storage


def _has_aws_signature(url: str) -> bool:
    return "X-Amz-Signature" in url or "X-Amz-Credential" in url


def _rewrite_host(url: str, base: str) -> str:
    parsed = urlparse(url)
    base = base.rstrip("/")
    base_parsed = urlparse(base)
    return urlunparse(
        (
            base_parsed.scheme or parsed.scheme,
            base_parsed.netloc or parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def _presign_with_public_base(storage: Storage, name: str, public_base: str) -> str | None:
    """Generate a presigned URL that uses the public base host.

    When the storage backend signs URLs against an internal host (e.g.,
    ``http://minio:9000``), simply rewriting the host breaks the signature.
    This helper regenerates a signature using ``MEDIA_PUBLIC_BASE_URL`` so the
    resulting URL stays valid for browsers.
    """
    try:
        from storages.backends.s3boto3 import S3Boto3Storage
    except ImportError:
        return None

    if not isinstance(storage, S3Boto3Storage):
        return None
    if not getattr(storage, "querystring_auth", False):
        return None
    if not public_base:
        return None

    try:
        import boto3
        from botocore.config import Config

        use_ssl = public_base.startswith("https://")
        config = Config(
            signature_version=getattr(settings, "AWS_S3_SIGNATURE_VERSION", "s3v4"),
            s3={"addressing_style": getattr(settings, "AWS_S3_ADDRESSING_STYLE", "auto")},
        )

        client = boto3.client(
            "s3",
            endpoint_url=public_base,
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
            use_ssl=use_ssl,
            config=config,
        )

        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": name},
            ExpiresIn=getattr(storage, "querystring_expire", 3600),
            HttpMethod="GET",
        )
    except Exception:
        # Fall back to the original URL if presigning with the public host fails.
        return None


class StorageService:
    def __init__(self, storage: Storage = default_storage):
        self._storage = storage

    def url(self, name: str, request=None) -> str:
        """Return a browser-ready URL for the stored object.

        - Keeps presigned URLs intact (or re-signs them for a public host).
        - Builds absolute URLs for relative paths when a request is provided.
        - Optionally rewrites hosts using MEDIA_PUBLIC_BASE_URL for public buckets.
        """
        base = getattr(settings, "MEDIA_PUBLIC_BASE_URL", "").rstrip("/")

        url = self._storage.url(name)

        # If we need a public-facing host and the storage signed the URL against
        # an internal hostname, regenerate a signature using the public host.
        if base:
            presigned = _presign_with_public_base(self._storage, name, base)
            if presigned:
                url = presigned

        # If storage gives relative, build absolute from request when available
        if url.startswith("/") and request:
            url = request.build_absolute_uri(url)

        # If public base URL is provided and URL is not presigned, rewrite host
        if base and not _has_aws_signature(url):
            url = _rewrite_host(url, base)

        return url

    def delete(self, name: str) -> None:
        self._storage.delete(name)

    def size(self, name: str) -> int:
        return self._storage.size(name)


storage_service = StorageService()

try:
    from storages.backends.s3boto3 import S3Boto3Storage

    class PublicRewritingS3Boto3Storage(S3Boto3Storage):
        """
        Custom storage backend that automatically rewrites the host for all
        FileField.url calls without needing to pass through storage_service.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Ensure the bucket exists and is public
            try:
                self.connection.head_bucket(Bucket=self.bucket_name)
            except self.connection.exceptions.NoSuchBucket:
                self.connection.create_bucket(Bucket=self.bucket_name)
                # Set public read policy
                try:
                    self.connection.put_bucket_policy(
                        Bucket=self.bucket_name,
                        Policy=json.dumps({
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Principal": "*",
                                    "Action": "s3:GetObject",
                                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                                }
                            ]
                        })
                    )
                except Exception:
                    pass
            except Exception:
                # Ignore other errors, like permissions
                pass

        def url(self, name, parameters=None, expire=None, http_method=None):
            url = super().url(name, parameters, expire, http_method)

            base = getattr(settings, "MEDIA_PUBLIC_BASE_URL", "").rstrip("/")
            if not base:
                return url

            # Re-sign using the public host when URLs are presigned; otherwise,
            # rewrite the host only for unsigned/public buckets.
            presigned = _presign_with_public_base(self, name, base)
            if presigned:
                return presigned

            if not _has_aws_signature(url):
                return _rewrite_host(url, base)

            return url
except ImportError:
    pass
