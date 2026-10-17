import 'package:flutter/material.dart';
import 'package:pisec_client/globals/notifier_provider.dart';
import 'package:pisec_client/models/api/queryables/user_query.dart';
import 'package:pisec_client/models/api/responses/user_response.dart';
import 'package:pisec_client/repositories/api/generic/user_repository.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';
import 'package:pisec_client/widgets/dangerous_button.dart';
import 'package:pisec_client/widgets/delete_submit_dialog.dart';

class ProfilePage extends StatefulWidget {
  final UserRepository userRepository;
  final String initialEmail;

  const ProfilePage({
    super.key,
    required this.userRepository,
    this.initialEmail = "",
  });

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  late final UserResponse? _user;

  bool _passwordHidden = true;

  @override
  void initState() {
    super.initState();
    _emailController.text = widget.initialEmail;
    _loadUser();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _loadUser() async {
    try {
      final response = await widget.userRepository.getCurrentUser();

      // Required because we are using context more than once in async
      if (!mounted) return;

      setState(() {
        _user = response;
        _emailController.text = response.email;
      });
    } catch (e) {
      // TODO: Improve error handling here

      // Required because we are using context more than once in async
      if (!mounted) return;

      setState(() {
        _user = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    const spacing = 12.0;

    return Scaffold(
      appBar: AppBar(title: const Text("Profile")),
      body: Form(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(spacing),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                spacing: spacing,
                children: [
                  Text(
                    "Edit account details",
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 2 * spacing),
                  TextFormField(
                    decoration: const InputDecoration(
                      labelText: 'User email',
                      border: OutlineInputBorder(),
                    ),
                    controller: _emailController,
                    onFieldSubmitted: (_) async => await _onSubmit(context),
                  ),
                  TextFormField(
                    decoration: InputDecoration(
                      labelText: 'Password',
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        onPressed: () =>
                            setState(() => _passwordHidden = !_passwordHidden),
                        icon: Icon(
                          _passwordHidden
                              ? Icons.visibility
                              : Icons.visibility_off,
                        ),
                        tooltip: _passwordHidden
                            ? "Show password"
                            : "Hide password",
                      ),
                    ),
                    controller: _passwordController,
                    obscureText: _passwordHidden,
                    onFieldSubmitted: (_) async => await _onSubmit(context),
                  ),
                  TextFormField(
                    decoration: InputDecoration(
                      labelText: 'Confirm password',
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        onPressed: () =>
                            setState(() => _passwordHidden = !_passwordHidden),
                        icon: Icon(
                          _passwordHidden
                              ? Icons.visibility
                              : Icons.visibility_off,
                        ),
                        tooltip: _passwordHidden
                            ? "Show password"
                            : "Hide password",
                      ),
                    ),
                    controller: _confirmPasswordController,
                    obscureText: _passwordHidden,
                    onFieldSubmitted: (_) async => await _onSubmit(context),
                  ),
                  const SizedBox(height: spacing),
                  Row(
                    spacing: spacing,
                    children: [
                      FilledButton(
                        onPressed: () async => await _onSubmit(context),
                        child: const Text("Update profile"),
                      ),
                      DangerousButton.outline(
                        onPressed: () async => await _onDelete(context),
                        child: const Text("Delete account"),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _onSubmit(BuildContext context) async {
    if (_passwordController.text != _confirmPasswordController.text) {
      // TODO: Display error message via toast or popup
      return;
    }

    // TODO: Handle invalid emails
    final String? emailText = _emailController.text == widget.initialEmail
        ? null
        : (_emailController.text.isEmpty ? null : _emailController.text);
    final query = UserQuery(
      email: emailText,
      password: _passwordController.text,
    );

    try {
      await widget.userRepository.updateCurrentUser(query);
    } catch (e) {
      // If user details haven't changed, then there is nothing to do
      // TODO: Display error message via toast or popup
      return;
    }

    if (emailText != null) {
      // Required because we are using context more than once in async
      if (!context.mounted) return;

      final authVM = NotifierProvider.of<AuthViewModel>(context);
      await authVM.reLogin(
        UserQuery(email: emailText, password: _passwordController.text),
      );
    }

    // Required because we are using context more than once in async
    if (!context.mounted) return;

    Navigator.pop(context);
  }

  Future<void> _onDelete(BuildContext context) async {
    final email = _user?.email ?? _emailController.text;

    final confirmed = await showDeleteDialog(
      context,
      title: const Text("Delete account?"),
      subtitle: const Text("Are you sure you want to delete your account?"),
      textToDelete: email,
      deleteButtonText: "Delete",
      onSubmit: () async => await widget.userRepository.deleteCurrentUser(),
    );

    if (confirmed) {
      if (!context.mounted) return;

      // Set the authenticaed status as false (account no longer exists)
      // This will automatically redirect to the login page
      final authVM = NotifierProvider.of<AuthViewModel>(context);
      await authVM.assertAuthenticated();
    }
  }
}
