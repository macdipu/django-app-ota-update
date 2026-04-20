class UpdateModel {
  final int id;
  final String version;
  final int buildNumber;
  final String apkUrl;
  final bool forceUpdate;
  final String changelog;
  final String minSupportedVersion;
  final DateTime createdAt;

  UpdateModel({
    required this.id,
    required this.version,
    required this.buildNumber,
    required this.apkUrl,
    required this.forceUpdate,
    required this.changelog,
    required this.minSupportedVersion,
    required this.createdAt,
  });

  factory UpdateModel.fromJson(Map<String, dynamic> json) {
    return UpdateModel(
      id: json['id'] as int,
      version: json['version'] as String? ?? '',
      buildNumber: (json['build_number'] is String)
          ? int.tryParse(json['build_number']) ?? 0
          : (json['build_number'] as int? ?? 0),
      apkUrl: json['apk_url'] as String? ?? '',
      forceUpdate: json['force_update'] as bool? ?? false,
      changelog: json['changelog'] as String? ?? '',
      minSupportedVersion: json['min_supported_version'] as String? ?? '',
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'version': version,
        'build_number': buildNumber,
        'apk_url': apkUrl,
        'force_update': forceUpdate,
        'changelog': changelog,
        'min_supported_version': minSupportedVersion,
        'created_at': createdAt.toIso8601String(),
      };
}

