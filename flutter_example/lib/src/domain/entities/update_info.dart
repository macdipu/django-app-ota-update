class UpdateInfo {
  final int id;
  final String version;
  final int buildNumber;
  final String apkUrl;
  final bool forceUpdate;
  final String changelog;
  final String minSupportedVersion;
  final DateTime createdAt;

  UpdateInfo({
    required this.id,
    required this.version,
    required this.buildNumber,
    required this.apkUrl,
    required this.forceUpdate,
    required this.changelog,
    required this.minSupportedVersion,
    required this.createdAt,
  });
}

