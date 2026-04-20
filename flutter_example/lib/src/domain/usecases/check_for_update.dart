import '../entities/update_info.dart';
import '../repositories/update_repository.dart';

class CheckForUpdate {
  final UpdateRepository repository;

  CheckForUpdate(this.repository);

  Future<UpdateInfo?> call() async {
    return await repository.checkForUpdate();
  }
}

