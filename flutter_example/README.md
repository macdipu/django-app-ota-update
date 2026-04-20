Update Manager
================

Standalone in-app OTA update module using ota_update, package_info_plus and clean architecture.

Quick start

- Add `in_update_manager` as a local package or copy code into your project.
- Example app is in `example/` folder. Run example with `flutter run` from that folder (add flutter project config as needed).

Android notes

This package uses `ota_update` which requires additional Android manifest/provider entries for PackageInstaller and file provider if you want package installer or silent installs. See ota_update package README for exact Android manifest changes (filepaths.xml, provider and receiver). Also enable coreLibraryDesugaring if using Java 8 features as described by ota_update docs.

    <!-- Required permissions for OTA update -->
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>