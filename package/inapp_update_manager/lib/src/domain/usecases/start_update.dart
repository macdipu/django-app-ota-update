import 'package:ota_update/ota_update.dart';
import '../repositories/update_repository.dart';

class StartUpdate {
  final UpdateRepository repository;

  StartUpdate(this.repository);

  Stream<OtaEvent> call(String apkUrl, {bool usePackageInstaller = true}) {
    return repository.startUpdate(apkUrl, usePackageInstaller: usePackageInstaller);
  }
}

