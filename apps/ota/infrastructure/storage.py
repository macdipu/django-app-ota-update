from django.conf import settings
from django.core.files.storage import default_storage


def _has_aws_signature(url: str) -> bool:
    return "X-Amz-Signature" in url or "X-Amz-Credential" in url


def _rewrite_host(url: str, base: str) -> str:
    from urllib.parse import urlparse, urlunparse
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


class StorageService:
    def __init__(self, storage=default_storage):
        self._storage = storage

    def url(self, name: str, request=None) -> str:
        url = self._storage.url(name)

        base = getattr(settings, "MEDIA_PUBLIC_BASE_URL", "").rstrip("/")

        # replace internal docker URL with public URL
        if base and "minio:9000" in url:
            return url.replace("http://minio:9000", base)

        return url

    def delete(self, name: str) -> None:
        self._storage.delete(name)

    def size(self, name: str) -> int:
        return self._storage.size(name)


try:
    from storages.backends.s3boto3 import S3Boto3Storage

    class PublicRewritingS3Boto3Storage(S3Boto3Storage):
        def url(self, name, parameters=None, expire=None, http_method=None):
            url = super().url(name, parameters, expire, http_method)

            base = getattr(settings, "MEDIA_PUBLIC_BASE_URL", "").rstrip("/")
            if not base:
                return url

            if not _has_aws_signature(url):
                return _rewrite_host(url, base)

            return url
except ImportError:
    pass


storage_service = StorageService()