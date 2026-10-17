import 'package:flutter/material.dart';
import 'package:pisec_client/routes/route_args/login_route_args.dart';
import 'package:pisec_client/screens/login_page.dart';
import 'package:pisec_client/types/auth_state.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';

class AuthRedirector extends StatefulWidget {
  final AuthViewModel authVM;
  final Widget child;

  const AuthRedirector({super.key, required this.authVM, required this.child});

  @override
  State<StatefulWidget> createState() => _AuthRedirectorState();
}

class _AuthRedirectorState extends State<AuthRedirector> {
  @override
  void initState() {
    super.initState();
    widget.authVM.addListener(_onAuthStateChanged);
  }

  @override
  void dispose() {
    widget.authVM.removeListener(_onAuthStateChanged);
    super.dispose();
  }

  void _onAuthStateChanged() {
    // Ensures the user is forced to login page if unauthenticated
    if (widget.authVM.authState == AuthState.disconnected &&
        widget.child is! LoginPage) {
      Navigator.of(context).pushNamedAndRemoveUntil(
        "/login",
        (route) => false,
        arguments: LoginRouteArgs(
          serverUrl: widget.authVM.serverUrl,
          email: widget.authVM.currentUser?.email ?? "",
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}
