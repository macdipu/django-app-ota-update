# in_update_manager

Reusable in-app OTA update manager for Flutter apps, built with `ota_update`, `package_info_plus`, and a clean architecture layout.

## What it provides

- Automatic update check and prompt UI via `AutoUpdateGate`.
- Optional or forced update behavior (`force_update` and `min_supported_version`).
- OTA APK download/install flow backed by `ota_update`.
- Simple backend contract: fetch update info from your API and compare app build number.

## Install

Add the package to your app (`path`, git, or hosted source depending on your setup).

```yaml
dependencies:
  in_update_manager:
    path: ../in_update_manager
```

Then install dependencies:

```bash
flutter pub get
```

## Basic usage

Wrap your app (or a screen) with `AutoUpdateGate`.

```dart
import 'package:in_update_manager/update_manager.dart';

AutoUpdateGate(
  baseUrl: 'https://your-api.example.com',
  packageName: 'com.example.app',
  enableInReleaseMode: true,
  child: const YourHome(),
)
```

### AutoUpdateGate parameters

- `child`: widget tree to render.
- `baseUrl`: backend host used for update checks.
- `packageName`: app package id sent to backend.
- `checkOnFirstFrame` (default `true`): checks right after first frame.
- `enableInReleaseMode` (default `false`): set to `true` to enable checks in release builds.

## Backend API contract

The data source calls:

- `GET {baseUrl}/api/update/?package={packageName}`

Expected JSON fields:

```json
{
  "id": 1,
  "version": "1.2.0",
  "build_number": 120,
  "apk_url": "https://cdn.example.com/app-release.apk",
  "force_update": false,
  "changelog": "Bug fixes and improvements",
  "min_supported_version": "1.1.0",
  "created_at": "2026-04-20T12:00:00Z"
}
```

Notes:

- Update is offered when `build_number` is greater than the installed app build number.
- Force update is triggered when `force_update` is `true` or current app version is below `min_supported_version`.

## Android setup (required)

For OTA install behavior, configure Android with the required permissions/components used by `ota_update`.

### 1) AndroidManifest permissions

```xml
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>
```

### 2) File provider and install receiver

Add provider + receiver entries under `<application>` (see the working example in `example/android/app/src/main/AndroidManifest.xml`).

### 3) Core library desugaring

Enable desugaring in `android/app/build.gradle(.kts)` and add:

```kotlin
coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
```

## Run the included example

The demo app is in `example/` and already wires `AutoUpdateGate`.

```bash
cd example
flutter pub get
flutter run
```

Update `example/lib/src_example/setup_example.dart` with your own API base URL and package name before testing against your backend.
