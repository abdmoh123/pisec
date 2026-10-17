import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:pisec_client/exceptions/http_exceptions.dart';
import 'package:pisec_client/globals/notifier_provider.dart';
import 'package:pisec_client/models/api/queryables/pagination_params.dart';
import 'package:pisec_client/models/api/responses/camera_credential_response.dart';
import 'package:pisec_client/models/api/responses/paginated_response.dart';
import 'package:pisec_client/models/api/responses/redacted_camera_credential_response.dart';
import 'package:pisec_client/repositories/api/generic/user_repository.dart';
import 'package:pisec_client/types/auth_state.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';
import 'package:pisec_client/widgets/credential_tile.dart';

class CredentialsPage extends StatefulWidget {
  final UserRepository userRepository;

  const CredentialsPage({super.key, required this.userRepository});

  @override
  State<StatefulWidget> createState() => _CredetialsPageState();
}

class _CredetialsPageState extends State<CredentialsPage> {
  Future<PaginatedResponse<RedactedCameraCredentialResponse>> future =
      Future.value(PaginatedResponse<RedactedCameraCredentialResponse>.empty());

  @override
  void initState() {
    super.initState();
    _refreshCredentials(listen: false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Credentials")),
      floatingActionButton: FloatingActionButton(
        child: Icon(Icons.add),
        onPressed: () async => await _newCredential(),
      ),
      body: SafeArea(
        child: FutureBuilder(
          future: future,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(child: Text(snapshot.error.toString()));
            }
            if (snapshot.hasData) {
              if (snapshot.data!.items.isEmpty) {
                return const Center(child: Text("No credentials found"));
              }
              return _buildCredentialsList(snapshot.data!.items);
            }
            return const Center(child: Text("Something went wrong"));
          },
        ),
      ),
    );
  }

  Widget _buildCredentialsList(
    List<RedactedCameraCredentialResponse> credentials,
  ) {
    return ListView.separated(
      itemCount: credentials.length,
      itemBuilder: (context, index) {
        return CredentialTile(
          credential: credentials[index],
          deleteCredential: () async =>
              await _deleteCredential(credentials[index].clientID),
        );
      },
      separatorBuilder: (context, index) => Divider(),
    );
  }

  Future<PaginatedResponse<RedactedCameraCredentialResponse>> _getCredentials({
    bool listen = true,
  }) async {
    final authVM = NotifierProvider.of<AuthViewModel>(context, listen: listen);
    await authVM.assertAuthenticated();

    // Should be displayed in the GUI automatically via FutureBuilder
    if (authVM.authState == AuthState.desynced) {
      throw FailedToConnectException("Failed to connect to server");
    }

    final response = await widget.userRepository.getCameraCredentials(
      PaginationParams(pageIndex: 0, pageSize: 1000),
    );
    return response;
  }

  void _refreshCredentials({bool listen = true}) {
    setState(() {
      future = _getCredentials(listen: listen);
    });
  }

  Future<void> _newCredential() async {
    CameraCredentialResponse response;
    try {
      response = await widget.userRepository.createCameraCredential();
    } catch (e) {
      // Do nothing for now if we couldn't create a new credential
      return;
    }

    _refreshCredentials();

    if (!mounted) return;

    showModalBottomSheet(
      context: context,
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(8.0),
          child: Column(
            children: [
              ListTile(
                title: const Text("Credential ID"),
                subtitle: Text(
                  response.clientID,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: IconButton(
                  onPressed: () =>
                      Clipboard.setData(ClipboardData(text: response.clientID)),
                  icon: const Icon(Icons.copy),
                ),
              ),
              ListTile(
                title: const Text("Credential secret"),
                subtitle: Text(
                  response.clientSecret,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: IconButton(
                  onPressed: () =>
                      Clipboard.setData(ClipboardData(text: response.clientID)),
                  icon: const Icon(Icons.copy),
                ),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton.icon(
                    onPressed: () async {
                      try {
                        await _deleteCredential(response.clientID);
                        if (!context.mounted) return;
                      } catch (e) {
                        // TODO: Display and log error
                      } finally {
                        Navigator.of(context).pop();
                      }
                    },
                    icon: const Icon(Icons.delete),
                    label: const Text("Delete"),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _deleteCredential(String clientID) async {
    try {
      await widget.userRepository.deleteCameraCredential(clientID);
      _refreshCredentials();
    } catch (e, st) {
      return Future.error(e, st);
    }
  }
}
