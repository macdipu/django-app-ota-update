import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/update_model.dart';

class UpdateRemoteDataSource {
  final String baseUrl;
  final http.Client client;

  UpdateRemoteDataSource({required this.baseUrl, http.Client? client}) : client = client ?? http.Client();

  /// Calls GET /api/update/?package=<packageName>
  Future<UpdateModel?> fetchUpdateInfo(String packageName) async {
    final url = Uri.parse('$baseUrl/api/update/?package=$packageName');
    final resp = await client.get(url, headers: {
      'Accept': 'application/json',
    });

    if (resp.statusCode == 200) {
      final body = json.decode(resp.body) as Map<String, dynamic>;
      return UpdateModel.fromJson(body);
    }

    return null;
  }
}

