import 'package:flutter/material.dart';
import 'package:pisec_client/main.dart';
import 'package:pisec_client/routes/route_args/credentials_route_args.dart';
import 'package:pisec_client/routes/route_args/login_route_args.dart';
import 'package:pisec_client/routes/route_args/profile_route_args.dart';
import 'package:pisec_client/routes/route_args/register_route_args.dart';
import 'package:pisec_client/screens/about_page.dart';
import 'package:pisec_client/screens/credentials_page.dart';
import 'package:pisec_client/screens/login_page.dart';
import 'package:pisec_client/screens/profile_page.dart';
import 'package:pisec_client/screens/register_page.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';
import 'package:pisec_client/widgets/helpers/auth_redirector.dart';

class RouteGenerator {
  final List<Widget> mainPages;
  final AuthViewModel authVM;

  const RouteGenerator({required this.mainPages, required this.authVM});

  Route<dynamic> generateRoutes(RouteSettings settings) {
    final args = settings.arguments;
    switch (settings.name) {
      case '/':
        if (args == null) {
          return _homePageRoute();
        }
        if (args is int && args >= 0 && args < 3) {
          return _homePageRoute(pageIdx: args);
        }
        return errorRoute(message: "Args for home page must be int or empty");
      case '/videos':
        return _homePageRoute(pageIdx: 0);
      case '/cameras':
        return _homePageRoute(pageIdx: 1);
      case '/settings':
        return _homePageRoute(pageIdx: 2);
      case '/profile':
        if (args == null || args is! ProfileRouteArgs) {
          return errorRoute(message: "Invalid profile page args");
        }

        return _protectedRoute(
          ProfilePage(
            userRepository: args.userRepository,
            initialEmail: args.initialEmail,
          ),
        );
      case '/credentials':
        if (args == null || args is! CredentialsRouteArgs) {
          return errorRoute(message: "Invalid credentials page args");
        }

        return _protectedRoute(
          CredentialsPage(userRepository: args.userRepository),
        );
      case '/login':
        if (args == null) {
          return _protectedRoute(const LoginPage());
        }

        if (args is! LoginRouteArgs) {
          return errorRoute(message: "Invalid login page args");
        }

        return MaterialPageRoute(
          builder: (_) => LoginPage(
            initialServerUrl: args.serverUrl,
            initialEmail: args.email,
          ),
        );
      case '/register':
        if (args == null || args is! RegisterRouteArgs) {
          return errorRoute(message: "Invalid register page args");
        }

        return MaterialPageRoute(
          builder: (_) => RegisterPage(
            authService: args.authService,
            initialServerUrl: args.serverUrl,
            initialEmail: args.email,
            onSubmitSuccess: args.onSubmitSuccess,
          ),
        );
      case '/about':
        return MaterialPageRoute(builder: (_) => AboutPage());
      case '/unfinished':
        return _unfinishedRoute();
      default:
        return errorRoute(message: "Invalid page route");
    }
  }

  Route<dynamic> errorRoute({String message = "Error has occured"}) {
    return MaterialPageRoute(
      builder: (_) {
        return Scaffold(
          appBar: AppBar(title: Text("Error")),
          body: Center(child: Text(message)),
        );
      },
    );
  }

  Route<dynamic> _unfinishedRoute() {
    return MaterialPageRoute(
      builder: (_) => Scaffold(
        appBar: AppBar(title: const Text("Unfinished page")),
        body: const Center(child: Text("This page is unfinished")),
      ),
    );
  }

  Route<dynamic> _protectedRoute(Widget child) {
    return MaterialPageRoute(
      builder: (context) => AuthRedirector(authVM: authVM, child: child),
    );
  }

  Route<dynamic> _homePageRoute({int pageIdx = 0}) {
    return _protectedRoute(
      MyHomePage(title: 'Pisec', pages: mainPages, initPageIndex: pageIdx),
    );
  }
}
