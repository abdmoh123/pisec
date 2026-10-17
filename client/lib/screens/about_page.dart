import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';

class AboutPage extends StatelessWidget {
  const AboutPage({super.key});

  static final Future<PackageInfo> _pInfo = PackageInfo.fromPlatform();

  @override
  Widget build(BuildContext context) {
    const double spacing = 12.0;
    final size = MediaQuery.sizeOf(context);
    return Scaffold(
      appBar: AppBar(title: const Text("About")),
      body: FutureBuilder(
        future: _pInfo,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text(snapshot.error.toString()));
          }
          if (!snapshot.hasData) {
            return const Center(child: Text("Something went wrong"));
          }
          final pInfo = snapshot.data!;

          return Center(
            child: Padding(
              padding: EdgeInsets.only(bottom: size.height * 0.15),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                spacing: spacing,
                children: [
                  Expanded(
                    child: Image.asset(
                      "assets/icon/icon.png",
                      fit: BoxFit.fitWidth,
                    ),
                  ),
                  Text(
                    "Pisec",
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  Text("version: ${pInfo.version}.${pInfo.buildNumber}"),
                  OutlinedButton.icon(
                    onPressed: () => _launchGitUrl(),
                    icon: const Icon(Icons.code),
                    label: const Text("Source"),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Future<void> _launchGitUrl() async {
    final gitUrl = Uri.parse("https://github.com/abdmoh123/pi-security-camera");

    try {
      if (await canLaunchUrl(gitUrl)) {
        await launchUrl(gitUrl, mode: LaunchMode.platformDefault);
      } else {
        // Failed to launch a URL, not much to do tbh
      }
    } catch (e) {
      // Nothing to do
    }
  }
}
