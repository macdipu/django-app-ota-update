import 'package:ota_update/ota_update.dart';
import '../entities/update_info.dart';

abstract class UpdateRepository {
  Future<UpdateInfo?> checkForUpdate();

  /// Starts the OTA update process for apkUrl and returns ota_update event stream
  Stream<OtaEvent> startUpdate(String apkUrl, {bool usePackageInstaller = true});
}

