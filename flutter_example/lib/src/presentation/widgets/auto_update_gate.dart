import 'package:flutter/material.dart';

import '../controllers/update_controller.dart';
import 'update_dialog.dart';

/// Wrap your screen/app with this widget to automatically check and prompt for updates.
class AutoUpdateGate extends StatefulWidget {
  final Widget child;
  final String baseUrl;
  final String packageName;
  final bool checkOnFirstFrame;

  const AutoUpdateGate({
    Key? key,
    required this.child,
    required this.baseUrl,
    required this.packageName,
    this.checkOnFirstFrame = true,
  }) : super(key: key);

  @override
  State<AutoUpdateGate> createState() => _AutoUpdateGateState();
}

class _AutoUpdateGateState extends State<AutoUpdateGate> {
  late final UpdateController _controller;
  bool _dialogOpen = false;
  int? _lastPromptedBuild;

  @override
  void initState() {
    super.initState();
    _controller = UpdateController.fromConfig(
      baseUrl: widget.baseUrl,
      packageName: widget.packageName,
    );

    if (widget.checkOnFirstFrame) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _checkAndPrompt();
      });
    }
  }

  Future<void> _checkAndPrompt() async {
    await _controller.checkForUpdate();
    if (!mounted) return;

    final info = _controller.updateInfo.value;
    if (!_controller.isUpdateAvailable.value || info == null || _dialogOpen) {
      return;
    }

    // For optional updates, do not re-prompt for the same build in this widget lifecycle.
    if (!_controller.isForceUpdate.value &&
        _lastPromptedBuild == info.buildNumber) {
      return;
    }

    _dialogOpen = true;
    _lastPromptedBuild = info.buildNumber;

    await showDialog<void>(
      context: context,
      barrierDismissible: !_controller.isForceUpdate.value,
      builder: (_) => UpdateDialog(controller: _controller),
    );

    _dialogOpen = false;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}
