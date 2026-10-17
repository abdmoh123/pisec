import 'package:flutter/material.dart';
import 'package:pisec_client/models/api/queryables/user_query.dart';
import 'package:pisec_client/services/login_api_service.dart';

enum _AppBarMenuActions { about }

class RegisterPage extends StatefulWidget {
  final LoginAPIService authService;
  final String initialServerUrl;
  final String initialEmail;

  final void Function(String serverUrl, String email)? _onSubmitSuccess;

  const RegisterPage({
    super.key,
    required this.authService,
    this.initialServerUrl = "",
    this.initialEmail = "",
    Function(String serverUrl, String email)? onSubmitSuccess,
  }) : _onSubmitSuccess = onSubmitSuccess;

  @override
  State<StatefulWidget> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _serverUrlController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  bool _passwordHidden = true;

  @override
  initState() {
    super.initState();
    _serverUrlController.text = widget.initialServerUrl;
    _emailController.text = widget.initialEmail;
  }

  @override
  dispose() {
    _serverUrlController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const spacing = 12.0;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Pisec - Register"),
        actions: [
          PopupMenuButton<_AppBarMenuActions>(
            onSelected: (value) {
              switch (value) {
                case _AppBarMenuActions.about:
                  Navigator.of(context).pushNamed('/about');
                  break;
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: _AppBarMenuActions.about,
                child: ListTile(
                  leading: Icon(Icons.info),
                  title: Text("About"),
                ),
              ),
            ],
          ),
        ],
      ),
      body: SafeArea(
        child: Form(
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
                      "Create a new account",
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 2 * spacing),
                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: 'Server host',
                        border: OutlineInputBorder(),
                      ),
                      controller: _serverUrlController,
                      onFieldSubmitted: (_) async => await _onSubmit(context),
                    ),
                    const SizedBox(height: spacing),
                    TextFormField(
                      decoration: const InputDecoration(
                        labelText: 'Email',
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
                          onPressed: () => setState(
                            () => _passwordHidden = !_passwordHidden,
                          ),
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
                          onPressed: () => setState(
                            () => _passwordHidden = !_passwordHidden,
                          ),
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
                    FilledButton(
                      onPressed: () async => await _onSubmit(context),
                      child: const Text("Register"),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _onSubmit(BuildContext context) async {
    // TODO: Display error message via toast or popup
    if (_passwordController.text != _confirmPasswordController.text) return;

    final userQuery = UserQuery(
      email: _emailController.text,
      password: _passwordController.text,
    );

    // Required because we are using context more than once in async
    if (!context.mounted) return;

    try {
      final response = await widget.authService.registerUser(userQuery);

      // Required because we are using context more than once in async
      if (!context.mounted) return;

      // Run on submit callback, which can be used to update a login page's text
      // inputs for the server url and user email address
      widget._onSubmitSuccess?.call(_serverUrlController.text, response.email);

      Navigator.of(context).pop();
    } catch (e) {
      // TODO: Display the error instead of doing nothing
    }
  }
}
