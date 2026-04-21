import 'dart:async';
import 'package:ota_update/ota_update.dart';
import '../../domain/entities/update_info.dart';
import '../../domain/repositories/update_repository.dart';
import '../datasources/update_remote_data_source.dart';
import '../models/update_model.dart';

class UpdateRepositoryImpl implements UpdateRepository {
  final UpdateRemoteDataSource remoteDataSource;
  final String packageName;
  final StreamController<bool> _downloadingController = StreamController<bool>.broadcast();
  Stream<bool> get downloadingStream => _downloadingController.stream;
  StreamSubscription<OtaEvent>? _currentSubscription;
  StreamController<OtaEvent>? _currentOtaController;

  UpdateRepositoryImpl({required this.remoteDataSource, required this.packageName});

  @override
  Future<UpdateInfo?> checkForUpdate() async {
    final UpdateModel? model = await remoteDataSource.fetchUpdateInfo(packageName);
    if (model == null) return null;
    return UpdateInfo(
      id: model.id,
      version: model.version,
      buildNumber: model.buildNumber,
      apkUrl: model.apkUrl,
      forceUpdate: model.forceUpdate,
      changelog: model.changelog,
      minSupportedVersion: model.minSupportedVersion,
      createdAt: model.createdAt,
    );
  }

  @override
  Stream<OtaEvent> startUpdate(String apkUrl, {bool usePackageInstaller = true}) {
    if (_currentSubscription != null) {
      return Stream<OtaEvent>.error(StateError('Another download (call) is already running'));
    }

    var downloadUrl = apkUrl;
    if (downloadUrl.startsWith('http://')) {
      downloadUrl = downloadUrl.replaceFirst(RegExp(r'^http:'), 'https:');
      print('[update_manager] Promoted APK URL to HTTPS: $downloadUrl');
    }
    final otaStream = OtaUpdate().execute(
      downloadUrl,
      destinationFilename: 'update_manager_download.apk',
      usePackageInstaller: usePackageInstaller,
    );

    final controller = StreamController<OtaEvent>();
    _currentOtaController = controller;

    try {
      _downloadingController.add(true);
    } catch (_) {}

    _currentSubscription = otaStream.listen(
      (event) {
        controller.add(event);
      },
      onError: (e, st) {
        controller.addError(e, st);
        _clearCurrentDownload();
      },
      onDone: () {
        controller.close();
        _clearCurrentDownload();
      },
      cancelOnError: false,
    );

    controller.onCancel = () async {
      await _currentSubscription?.cancel();
      controller.close();
      _clearCurrentDownload();
    };

    return controller.stream;
  }

  /// Cancel the current OTA download (if any). UI can call this when user
  /// taps a "Cancel" button while downloading.
  Future<void> cancelUpdate() async {
    await _currentSubscription?.cancel();
    try {
      _currentOtaController?.close();
    } catch (_) {}
    _clearCurrentDownload();
  }

  void _clearCurrentDownload() {
    _currentSubscription = null;
    _currentOtaController = null;
    // notify listeners that downloading stopped
    try {
      _downloadingController.add(false);
    } catch (_) {
      // ignore if controller is closed
    }
  }
}

