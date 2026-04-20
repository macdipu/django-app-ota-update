import 'dart:async';

import 'package:get/get.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:ota_update/ota_update.dart';

import '../../data/datasources/update_remote_data_source.dart';
import '../../data/repositories/update_repository_impl.dart';
import '../../domain/entities/update_info.dart';
import '../../domain/usecases/check_for_update.dart';
import '../../domain/usecases/start_update.dart';
import '../../domain/repositories/update_repository.dart';

class UpdateController extends GetxController {
  final CheckForUpdate checkForUpdateUseCase;
  final StartUpdate startUpdateUseCase;
  final UpdateRepository repository;

  UpdateController({
    required this.checkForUpdateUseCase,
    required this.startUpdateUseCase,
    required this.repository,
  });

  factory UpdateController.fromConfig({
    required String baseUrl,
    required String packageName,
  }) {
    final remote = UpdateRemoteDataSource(baseUrl: baseUrl);
    final repo = UpdateRepositoryImpl(
      remoteDataSource: remote,
      packageName: packageName,
    );

    final controller = UpdateController(
      checkForUpdateUseCase: CheckForUpdate(repo),
      startUpdateUseCase: StartUpdate(repo),
      repository: repo,
    );

    // If the concrete repository exposes a downloading stream, listen to it
    try {
      controller._downloadingSub = repo.downloadingStream.listen((val) {
        controller.isDownloading.value = val;
      });
    } catch (_) {}

    return controller;
  }

  final RxBool isUpdateAvailable = false.obs;
  final RxBool isForceUpdate = false.obs;
  final RxDouble progress = 0.0.obs;
  final RxString status = ''.obs;
  final RxString changelog = ''.obs;
  final Rxn<UpdateInfo> updateInfo = Rxn<UpdateInfo>();
  StreamSubscription<OtaEvent>? _otaSub;
  final RxBool isDownloading = false.obs;
  StreamSubscription<bool>? _downloadingSub;

  Future<void> checkForUpdate() async {
    try {
      final PackageInfo pi = await PackageInfo.fromPlatform();
      final int currentBuild = int.tryParse(pi.buildNumber) ?? 0;

      final info = await checkForUpdateUseCase();
      if (info == null) {
        isUpdateAvailable.value = false;
        return;
      }

      // check min_supported_version if provided
      if (info.minSupportedVersion.isNotEmpty) {
        // naive compare: if current version name smaller than minSupportedVersion -> force update
        try {
          final List<int> curParts =
              pi.version.split('.').map((e) => int.tryParse(e) ?? 0).toList();
          final List<int> minParts = info.minSupportedVersion
              .split('.')
              .map((e) => int.tryParse(e) ?? 0)
              .toList();
          bool smaller = false;
          for (int i = 0;
              i <
                  (minParts.length > curParts.length
                      ? minParts.length
                      : curParts.length);
              i++) {
            final a = (i < curParts.length) ? curParts[i] : 0;
            final b = (i < minParts.length) ? minParts[i] : 0;
            if (a < b) {
              smaller = true;
              break;
            } else if (a > b) {
              break;
            }
          }
          if (smaller) {
            isForceUpdate.value = true;
          }
        } catch (_) {}
      }

      if (info.buildNumber > currentBuild) {
        updateInfo.value = info;
        isUpdateAvailable.value = true;
        if (info.forceUpdate) isForceUpdate.value = true;
        changelog.value = info.changelog;
      } else {
        isUpdateAvailable.value = false;
      }
    } catch (e) {
      // network or other error -> silently fail for now
      isUpdateAvailable.value = false;
    }
  }

  void startUpdate() {
    final ui = updateInfo.value;
    if (ui == null) return;
    _otaSub?.cancel();
    progress.value = 0.0;
    // set initial status and mark downloading so UI updates immediately
    status.value = 'Starting...';
    isDownloading.value = true;

    _otaSub = startUpdateUseCase(ui.apkUrl).listen(
      (event) {
        if (event.status == OtaStatus.DOWNLOADING) {
          final val = event.value ?? '0';
          final intPerc = int.tryParse(val) ?? 0;
          progress.value = intPerc / 100.0;
          status.value = 'Downloading (${intPerc}%)';
        } else if (event.status == OtaStatus.INSTALLING) {
          status.value = 'Installing...';
        } else if (event.status == OtaStatus.INSTALLATION_DONE) {
          progress.value = 1.0;
          status.value = 'Installation complete';
          isDownloading.value = false;
        } else if (event.status == OtaStatus.DOWNLOAD_ERROR ||
            event.status == OtaStatus.INTERNAL_ERROR) {
          status.value = 'Error during update';
          isDownloading.value = false;
        }
      },
      onError: (e) {
        status.value = 'Update failed';
        isDownloading.value = false;
      },
      onDone: () {
        // ensure downloading flag cleared
        isDownloading.value = false;
      },
    );
  }

  void cancelUpdate() {
    _otaSub?.cancel();
    _otaSub = null;
    // forward cancel to repository implementation to stop the download work
    try {
      if (repository is UpdateRepositoryImpl) {
        (repository as UpdateRepositoryImpl).cancelUpdate();
      }
    } catch (_) {}
    status.value = 'Cancelled';
    isDownloading.value = false;
  }

  @override
  void onClose() {
    _otaSub?.cancel();
    _downloadingSub?.cancel();
    super.onClose();
  }

  @override
  void onInit() {
    super.onInit();
    // If the concrete repository exposes a downloading stream, listen to it
    try {
      if (repository is UpdateRepositoryImpl) {
        _downloadingSub = (repository as UpdateRepositoryImpl)
            .downloadingStream
            .listen((val) {
          isDownloading.value = val;
        });
      }
    } catch (_) {}
  }
}
