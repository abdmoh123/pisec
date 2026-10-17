import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:pisec_client/factories/downloader_factory.dart';
import 'package:pisec_client/globals/notifier_provider.dart';
import 'package:pisec_client/repositories/api/http/http_camera_repository.dart';
import 'package:pisec_client/repositories/api/http/http_user_repository.dart';
import 'package:pisec_client/repositories/api/http/http_video_repository.dart';
import 'package:pisec_client/repositories/server_config_repository.dart';
import 'package:pisec_client/repositories/token_repository.dart';
import 'package:pisec_client/routes/route_args/login_route_args.dart';
import 'package:pisec_client/routes/route_generator.dart';
import 'package:pisec_client/screens/cameras_page.dart';
import 'package:pisec_client/screens/settings_page.dart';
import 'package:pisec_client/screens/videos_page.dart';
import 'package:pisec_client/services/auth_http_client.dart';
import 'package:pisec_client/services/login_api_service.dart';
import 'package:pisec_client/services/task_id_generators.dart';
import 'package:pisec_client/types/auth_state.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final loginMemory = LoginMemoryRepository();
  String baseUrl = await loginMemory.getServerUrl();
  final tokenStorage = TokenRepository();
  final authService = LoginAPIService(baseUrl: baseUrl);

  final authVM = AuthViewModel(loginMemory, tokenStorage, authService);
  await authVM.assertAuthenticated();
  final client = AuthHttpClient(
    tokenStorage,
    authService,
    onAuthGivenUp: authVM.assertAuthenticated,
  );

  // Automatically chooses between web and native downloader
  final downloaderService = createDownloaderService(videoIdFromUrl);
  await downloaderService.init();

  final videoRepository = HttpVideoRepository(
    client,
    baseUrl,
    downloaderService,
  );
  final cameraRepository = HttpCameraRepository(client, baseUrl);
  final userRepository = HttpUserRepository(client, baseUrl);

  final List<Widget> pages = [
    VideosPage(videoRepository: videoRepository),
    CamerasPage(
      cameraRepository: cameraRepository,
      userRepository: userRepository,
    ),
    SettingsPage(userRepository: userRepository),
  ];

  final routeGenerator = RouteGenerator(mainPages: pages, authVM: authVM);

  // Required to display the date in the correct format
  initializeDateFormatting("en_GB");
  runApp(PisecApp(routeGenerator: routeGenerator, authVM: authVM));
}

class PisecApp extends StatelessWidget {
  final RouteGenerator routeGenerator;
  final AuthViewModel authVM;

  const PisecApp({
    super.key,
    required this.routeGenerator,
    required this.authVM,
  });

  @override
  Widget build(BuildContext context) {
    return NotifierProvider<AuthViewModel>(
      notifier: authVM,
      child: MaterialApp(
        title: 'Pisec',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.deepOrange,
            brightness: Brightness.dark,
          ),
        ),
        onGenerateInitialRoutes: ((initialRoute) {
          if (authVM.authState == AuthState.disconnected) {
            return [
              routeGenerator.generateRoutes(
                RouteSettings(
                  name: '/login',
                  arguments: LoginRouteArgs(
                    serverUrl: authVM.serverUrl,
                    email: authVM.currentUser?.email ?? "",
                  ),
                ),
              ),
            ];
          }
          return [routeGenerator.generateRoutes(RouteSettings(name: '/'))];
        }),
        onGenerateRoute: routeGenerator.generateRoutes,
        onUnknownRoute: (_) =>
            routeGenerator.errorRoute(message: "Invalid page route"),
      ),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({
    super.key,
    required this.title,
    required this.pages,
    this.initPageIndex = 0,
  });

  final String title;
  final List<Widget> pages;
  final int initPageIndex;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int pageIndex = 0;

  @override
  void initState() {
    super.initState();
    pageIndex = widget.initPageIndex;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text("${widget.title} - ${_getTitle(pageIndex)}"),
      ),
      body: Center(child: widget.pages[pageIndex]),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: pageIndex,
        items: [
          BottomNavigationBarItem(
            label: _getTitle(0),
            activeIcon: const Icon(Icons.camera_roll),
            icon: const Icon(Icons.camera_roll_outlined),
          ),
          BottomNavigationBarItem(
            label: _getTitle(1),
            activeIcon: const Icon(Icons.camera),
            icon: const Icon(Icons.camera_outlined),
          ),
          BottomNavigationBarItem(
            label: _getTitle(2),
            activeIcon: const Icon(Icons.settings),
            icon: const Icon(Icons.settings_outlined),
          ),
        ],
        onTap: _onTabTapped,
      ),
    );
  }

  String _getTitle(int index) {
    switch (index) {
      case 0:
        return "Videos";
      case 1:
        return "Cameras";
      case 2:
        return "Settings";
      default:
        return "Unknown";
    }
  }

  void _onTabTapped(int index) {
    setState(() {
      pageIndex = index;
    });
  }
}
