import io
import pytest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.ota.models import AppUpdate


def make_apk(name="app.apk", size_bytes=1024):
    """Create a minimal fake APK file for testing."""
    content = b"\x00" * size_bytes
    return SimpleUploadedFile(name, content, content_type="application/vnd.android.package-archive")


class LatestUpdateViewTests(TestCase):
    def test_returns_404_when_no_updates(self):
        response = self.client.get("/api/update/")
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_returns_latest_update(self):
        AppUpdate.objects.create(
            version="1.0.0",
            apk_file=make_apk("v1.apk"),
            force_update=False,
            changelog="Initial release",
        )
        AppUpdate.objects.create(
            version="1.1.0",
            apk_file=make_apk("v2.apk"),
            force_update=True,
            changelog="Bug fixes",
        )
        response = self.client.get("/api/update/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Must return the most recent one
        self.assertEqual(data["version"], "1.1.0")
        self.assertTrue(data["force_update"])
        self.assertIn("apk_url", data)
        self.assertIn("changelog", data)

    def test_apk_url_is_absolute(self):
        AppUpdate.objects.create(
            version="2.0.0",
            apk_file=make_apk("v3.apk"),
        )
        response = self.client.get("/api/update/")
        data = response.json()
        self.assertTrue(data["apk_url"].startswith("http"))


class UpdateHistoryViewTests(TestCase):
    def test_returns_empty_list_when_no_updates(self):
        response = self.client.get("/api/updates/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_returns_all_updates_newest_first(self):
        AppUpdate.objects.create(version="1.0.0", apk_file=make_apk("v1.apk"))
        AppUpdate.objects.create(version="1.1.0", apk_file=make_apk("v2.apk"))
        response = self.client.get("/api/updates/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["version"], "1.1.0")  # latest first
