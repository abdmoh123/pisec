import 'package:flutter/material.dart';
import 'package:pisec_client/globals/notifier_provider.dart';
import 'package:pisec_client/models/api/queryables/user_query.dart';
import 'package:pisec_client/routes/route_args/register_route_args.dart';
import 'package:pisec_client/types/auth_state.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';

enum _AppBarMenuActions { about }

class LoginPage extends StatefulWidget {
  final String initialServerUrl;
  final String initialEmail;

  const LoginPage({
    super.key,
    this.initialServerUrl = "",
    this.initialEmail = "",
  });

  @override
  State<StatefulWidget> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _serverUrlController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

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
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const spacing = 12.0;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Pisec - Login"),
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
                    "Sign in to your Pisec server",
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
                  const SizedBox(height: spacing),
                  Row(
                    spacing: spacing,
                    children: [
                      FilledButton(
                        onPressed: () async => await _onSubmit(context),
                        child: const Text("Sign in"),
                      ),
                      OutlinedButton(
                        onPressed: () => Navigator.of(context).pushNamed(
                          '/register',
                          arguments: RegisterRouteArgs(
                            authService: NotifierProvider.of<AuthViewModel>(
                              context,
                            ).loginService,
                            serverUrl: _serverUrlController.text,
                            email: _emailController.text,
                            onSubmitSuccess: (serverUrl, email) {
                              // After registering was successful, automatically
                              // set the server url and email to use the one
                              // from the register page
                              _serverUrlController.text = serverUrl;
                              _emailController.text = email;
                            },
                          ),
                        ),
                        child: const Text("Register"),
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
    final userQuery = UserQuery(
      email: _emailController.text,
      password: _passwordController.text,
    );

    // TODO: Improve how invalid input is handled
    final authVM = NotifierProvider.of<AuthViewModel>(context);
    await authVM.login(_serverUrlController.text, userQuery);

    // Required because we are using context more than once in async
    if (!context.mounted) return;

    if (authVM.authState != AuthState.connected) {
      _passwordController.clear();
      return;
    }

    Navigator.of(context).pushNamedAndRemoveUntil("/", (route) => false);
  }
}
