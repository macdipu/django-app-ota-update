import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../controllers/update_controller.dart';

class UpdateDialog extends StatelessWidget {
  final UpdateController controller;

  const UpdateDialog({Key? key, required this.controller}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final info = controller.updateInfo.value;
      if (info == null) return const SizedBox.shrink();

      return AlertDialog(
        title: const Text('Update Available'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Version: ${info.version}'),
            const SizedBox(height: 8),
            Text(info.changelog),
            const SizedBox(height: 12),
            Obx(() {
              final status = controller.status.value;
              final prog = controller.progress.value;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (status.isNotEmpty) Text(status),
                  const SizedBox(height: 6),
                  LinearProgressIndicator(value: prog > 0 ? prog : null),
                ],
              );
            }),
          ],
        ),
        actions: _buildActions(context),
      );
    });
  }

  List<Widget> _buildActions(BuildContext context) {
    final force = controller.isForceUpdate.value;
    final downloading = controller.isDownloading.value;
    if (force) {
      return [
        ElevatedButton(
          onPressed: downloading ? null : () => controller.startUpdate(),
          child: downloading ? const Text('Updating...') : const Text('Update'),
        ),
      ];
    }

    return [
      TextButton(
        onPressed: () {
          Get.back();
        },
        child: const Text('Later'),
      ),
      if (!controller.isDownloading.value)
        ElevatedButton(
          onPressed: () {
            controller.startUpdate();
          },
          child: const Text('Update'),
        ),
      if (controller.isDownloading.value)
        ElevatedButton(
          onPressed: () {
            controller.cancelUpdate();
          },
          child: const Text('Cancel'),
        ),
    ];
  }
}

