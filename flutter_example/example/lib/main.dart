import 'package:flutter/material.dart';
import 'package:get/get.dart';

import 'package:update_manager/update_manager.dart';
import 'src_example/setup_example.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'Update Manager Example',
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  Widget build(BuildContext context) {
    return AutoUpdateGate(
      baseUrl: exampleBaseUrl,
      packageName: examplePackageName,
      child: Scaffold(
        appBar: AppBar(title: Text('Update Manager Example')),
        body: Center(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'AutoUpdateGate checks for updates after first frame and shows UpdateDialog automatically when needed.',
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
    );
  }
}
