import 'package:flutter/material.dart';
import 'package:pisec_client/exceptions/http_exceptions.dart';
import 'package:pisec_client/globals/notifier_provider.dart';
import 'package:pisec_client/models/api/queryables/pagination_params.dart';
import 'package:pisec_client/models/api/responses/camera_response.dart';
import 'package:pisec_client/models/api/responses/camera_subscription_response.dart';
import 'package:pisec_client/models/api/responses/paginated_response.dart';
import 'package:pisec_client/models/api/responses/user_response.dart';
import 'package:pisec_client/models/api/sortables/camera_fields.dart';
import 'package:pisec_client/models/sortable.dart';
import 'package:pisec_client/repositories/api/generic/camera_repository.dart';
import 'package:pisec_client/repositories/api/generic/user_repository.dart';
import 'package:pisec_client/types/auth_state.dart';
import 'package:pisec_client/types/sort_direction.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';
import 'package:pisec_client/widgets/camera_tile.dart';
import 'package:pisec_client/widgets/delete_submit_dialog.dart';

class CamerasPage extends StatefulWidget {
  final CameraRepository cameraRepository;
  final UserRepository userRepository;

  const CamerasPage({
    super.key,
    required this.cameraRepository,
    required this.userRepository,
  });

  @override
  State<StatefulWidget> createState() => _CamerasPageState();
}

class _CamerasPageState extends State<CamerasPage> {
  Future<PaginatedResponse<CameraResponse>> futureCameras = Future.value(
    PaginatedResponse<CameraResponse>.empty(),
  );

  List<CameraResponse> ownedCameras = [];

  CameraFields _sortBy = CameraFields.date;
  SortDirection _sortDirection = SortDirection.descending;

  Sortable<CameraFields> get _sortable =>
      Sortable<CameraFields>(field: _sortBy, direction: _sortDirection);

  Widget get _sortDirectionIcon {
    switch (_sortDirection) {
      case SortDirection.ascending:
        return const Icon(Icons.arrow_upward);
      case SortDirection.descending:
        return const Icon(Icons.arrow_downward);
    }
  }

  int currentPage = 1;
  int maxPages = 1;

  @override
  void initState() {
    super.initState();
    _refreshCameras();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                DropdownButton<CameraFields>(
                  padding: const EdgeInsets.fromLTRB(12.0, 0.0, 12.0, 0.0),
                  value: _sortBy,
                  items: [
                    const DropdownMenuItem(
                      value: CameraFields.date,
                      child: Text("By date"),
                    ),
                    const DropdownMenuItem(
                      value: CameraFields.name,
                      child: Text("By name"),
                    ),
                    const DropdownMenuItem(
                      value: CameraFields.camera,
                      child: Text("By camera"),
                    ),
                  ],
                  underline: Container(),
                  icon: const Icon(Icons.sort),
                  onChanged: (value) async {
                    setState(() {
                      _sortBy = value!;
                    });
                    await _refreshCameras();
                  },
                ),
                IconButton(
                  onPressed: () async {
                    setState(() {
                      _sortDirection = _sortDirection == SortDirection.ascending
                          ? SortDirection.descending
                          : SortDirection.ascending;
                    });
                    await _refreshCameras();
                  },
                  icon: _sortDirectionIcon,
                ),
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              spacing: 8.0,
              children: [
                IconButton(
                  onPressed: () async => _refreshCameras(),
                  icon: Icon(Icons.refresh),
                ),
              ],
            ),
          ],
        ),
        Expanded(
          child: FutureBuilder(
            future: futureCameras,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Center(child: Text(snapshot.error.toString()));
              }
              if (snapshot.hasData) {
                if (snapshot.data!.items.isEmpty) {
                  return const Center(child: Text("No cameras found"));
                }
                return _buildCameraList(snapshot.data!.items);
              }
              return const Center(child: Text("Something went wrong"));
            },
          ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          spacing: 8.0,
          children: [_buildPaginationGroup(context)],
        ),
      ],
    );
  }

  Widget _buildPaginationGroup(BuildContext context) {
    List<Widget> children = [];

    final toFirstPage = currentPage == 1 ? null : () => _toPage(1);
    final toPreviousPage = currentPage == 1 ? null : _previousPage;
    children.add(
      IconButton(onPressed: toFirstPage, icon: Icon(Icons.first_page)),
    );
    children.add(
      IconButton(onPressed: toPreviousPage, icon: Icon(Icons.chevron_left)),
    );

    if (currentPage > 2) {
      children.add(
        TextButton(
          onPressed: () => _toPage(currentPage - 2),
          child: Text((currentPage - 2).toString()),
        ),
      );
    }
    if (currentPage > 1) {
      children.add(
        TextButton(
          onPressed: () => _toPage(currentPage - 1),
          child: Text((currentPage - 1).toString()),
        ),
      );
    }

    children.add(
      TextButton(
        onPressed: () => _toPage(currentPage),
        style: ButtonStyle(
          backgroundColor: WidgetStatePropertyAll<Color>(
            Theme.of(context).colorScheme.inversePrimary,
          ),
        ),
        child: Text(currentPage.toString()),
      ),
    );

    if (currentPage < maxPages - 1) {
      children.add(
        TextButton(
          onPressed: () => _toPage(currentPage + 1),
          child: Text((currentPage + 1).toString()),
        ),
      );
    }
    if (currentPage < maxPages - 2) {
      children.add(
        TextButton(
          onPressed: () => _toPage(currentPage + 2),
          child: Text((currentPage + 2).toString()),
        ),
      );
    }

    final toLastPage = currentPage == maxPages ? null : () => _toPage(maxPages);
    final toNextPage = currentPage == maxPages ? null : _nextPage;
    children.add(
      IconButton(onPressed: toNextPage, icon: Icon(Icons.chevron_right)),
    );
    children.add(
      IconButton(onPressed: toLastPage, icon: Icon(Icons.last_page)),
    );

    return Row(children: children);
  }

  Widget _buildCameraList(List<CameraResponse> cameras) {
    return ListView.separated(
      itemCount: cameras.length,
      itemBuilder: (context, index) => CameraTile(
        camera: cameras[index],
        subscribeToCamera: (ownedCameras.contains(cameras[index]))
            ? (camera) => _onCameraSubscribe(camera)
            : null,
        unSubscribeToCamera: (ownedCameras.contains(cameras[index]))
            ? null
            : (cameraID) => _onCameraUnsubscribe(cameraID),
      ),
      separatorBuilder: (context, index) => Divider(),
    );
  }

  Future<PaginatedResponse<CameraResponse>> _getAllCameras({
    int? page,
    int pageSize = 10,
    bool onlyOwned = false,
  }) async {
    page = page ?? currentPage;

    final authVM = NotifierProvider.of<AuthViewModel>(context);
    await authVM.assertAuthenticated();

    // Should be displayed in the GUI automatically via FutureBuilder
    if (authVM.authState == AuthState.desynced) {
      _resetPagination();
      throw FailedToConnectException("Failed to connect to server");
    }

    try {
      final response = await widget.cameraRepository.getCurrentUserCameras(
        onlyOwned: onlyOwned,
        orderBy: _sortable,
        pagination: PaginationParams(pageIndex: page - 1, pageSize: pageSize),
      );
      if (mounted) {
        setState(() => maxPages = response.totalPages);
      }
      return response;
    } catch (e) {
      _resetPagination();
      rethrow;
    }
  }

  void _toPage(int page) {
    if (page == currentPage) {
      return;
    }
    setState(() {
      currentPage = page;
      futureCameras = _getAllCameras();
    });
  }

  void _nextPage() {
    if (currentPage == maxPages) {
      return;
    }
    _toPage(currentPage + 1);
  }

  void _previousPage() {
    if (currentPage == 1) {
      return;
    }
    _toPage(currentPage - 1);
  }

  void _resetPagination() {
    if (!mounted) return;
    setState(() {
      currentPage = 1;
      maxPages = 0;
    });
  }

  Future<void> _refreshCameras() async {
    final ownedCamerasResponse = await _getAllCameras(
      onlyOwned: true,
      pageSize: 1000,
    );
    setState(() {
      futureCameras = _getAllCameras();
      ownedCameras = ownedCamerasResponse.items;
    });
  }

  Future<void> _onCameraSubscribe(CameraResponse camera) async {
    final newUserController = TextEditingController();

    // TODO: Make use of the result of the function call
    await showAdaptiveDialog(
      context: context,
      barrierDismissible: true,
      builder: (context) {
        return AlertDialog(
          title: const Text("Subscribe a user to this camera"),
          content: Column(
            children: [
              TextField(
                controller: newUserController,
                autofocus: true,
                decoration: const InputDecoration(
                  labelText: "User email",
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            FilledButton(
              onPressed: () async {
                try {
                  await _subscribeCameraToUser(
                    newUserController.text,
                    camera.id,
                  );

                  if (!context.mounted) return;

                  Navigator.of(context).pop(true);
                } catch (e) {
                  Navigator.of(context).pop(false);
                }
              },
              child: const Text("Subscribe"),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text("Cancel"),
            ),
          ],
        );
      },
    );

    newUserController.dispose();
  }

  Future<void> _onCameraUnsubscribe(CameraResponse camera) async {
    final confirmed = await showDeleteDialog(
      context,
      title: const Text("Unsubscribe from camera?"),
      subtitle: Text(
        "Are you sure you want to unsubscribe from ${camera.name}?",
      ),
      textToDelete: camera.name,
      deleteButtonText: "Unsubscribe",
      onSubmit: () async => await _unsubscribeCamera(camera.id),
    );

    if (confirmed) {
      await _refreshCameras();
    }
  }

  Future<CameraSubscriptionResponse> _subscribeCameraToUser(
    String username,
    int cameraID,
  ) async {
    final users = await widget.userRepository.getUsersByName(username);

    late final UserResponse? userToSubscribe;
    for (var user in users.items) {
      if (user.email == username) {
        userToSubscribe = user;
        break;
      }
    }

    // Throw error if no user was found with matching email/username
    if (userToSubscribe == null) {
      // TODO: Use or create a more relevant exception type
      throw HttpCodedException(statusCode: 404, message: "User not found");
    }

    return await widget.cameraRepository.subscribeToCamera(
      userToSubscribe.id,
      cameraID,
    );
  }

  Future<CameraSubscriptionResponse> _unsubscribeCamera(int cameraID) async {
    final user = await widget.userRepository.getCurrentUser();

    return await widget.cameraRepository.unsubscribeFromCamera(
      user.id,
      cameraID,
    );
  }
}
