import 'package:flutter/material.dart';
import 'package:pisec_client/globals/notifier_provider.dart';
import 'package:pisec_client/repositories/api/generic/user_repository.dart';
import 'package:pisec_client/routes/route_args/credentials_route_args.dart';
import 'package:pisec_client/routes/route_args/profile_route_args.dart';
import 'package:pisec_client/types/auth_state.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';
import 'package:pisec_client/widgets/dangerous_button.dart';

class SettingsPage extends StatefulWidget {
  final UserRepository userRepository;

  const SettingsPage({super.key, required this.userRepository});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _isAuthenticated = false;

  @override
  void initState() {
    super.initState();
    _checkAuth(listen: false);
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        ListTile(
          leading: const Icon(Icons.account_circle),
          title: const Text("Profile"),
          subtitle: const Text("Change account details"),
          onTap: _isAuthenticated
              ? () => Navigator.pushNamed(
                  context,
                  '/profile',
                  arguments: ProfileRouteArgs(
                    userRepository: widget.userRepository,
                    initialEmail:
                        NotifierProvider.of<AuthViewModel>(
                          context,
                          listen: false,
                        ).currentUser?.email ??
                        "",
                  ),
                )
              : null,
        ),
        ListTile(
          leading: const Icon(Icons.key),
          title: const Text("Credentials"),
          subtitle: const Text("Manage camera credentials"),
          onTap: _isAuthenticated
              ? () => Navigator.pushNamed(
                  context,
                  '/credentials',
                  arguments: CredentialsRouteArgs(
                    userRepository: widget.userRepository,
                  ),
                )
              : null,
        ),
        ListTile(
          leading: const Icon(Icons.info),
          title: const Text("About"),
          subtitle: const Text("View app and server info"),
          onTap: () => Navigator.pushNamed(context, '/about'),
        ),
        Center(
          child: FittedBox(
            child: Padding(
              padding: const EdgeInsets.all(8.0),
              child: DangerousButton.outline(
                onPressed: () async => await _logout(context),
                child: const Row(
                  children: [Icon(Icons.logout), Text("Sign out")],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _checkAuth({bool listen = true}) async {
    final authVM = NotifierProvider.of<AuthViewModel>(context, listen: listen);
    await authVM.assertAuthenticated();

    if (!mounted) return;
    setState(() => _isAuthenticated = authVM.authState == AuthState.connected);
  }

  Future<void> _logout(BuildContext context) async {
    final authVM = NotifierProvider.of<AuthViewModel>(context);
    await authVM.logout();
  }
}
