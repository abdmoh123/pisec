import 'dart:async';

import 'package:flutter/material.dart';
import 'package:pisec_client/exceptions/http_exceptions.dart';
import 'package:pisec_client/globals/notifier_provider.dart';
import 'package:pisec_client/models/api/queryables/pagination_params.dart';
import 'package:pisec_client/models/api/queryables/video_query.dart';
import 'package:pisec_client/models/api/responses/paginated_response.dart';
import 'package:pisec_client/models/api/responses/video_response.dart';
import 'package:pisec_client/models/api/sortables/video_fields.dart';
import 'package:pisec_client/models/sortable.dart';
import 'package:pisec_client/repositories/api/generic/video_repository.dart';
import 'package:pisec_client/types/auth_state.dart';
import 'package:pisec_client/types/sort_direction.dart';
import 'package:pisec_client/viewmodels/auth_view_model.dart';
import 'package:pisec_client/widgets/video_tile.dart';

class VideosPage extends StatefulWidget {
  final VideoRepository videoRepository;

  const VideosPage({super.key, required this.videoRepository});

  @override
  State<StatefulWidget> createState() => _VideosPageState();
}

class _VideosPageState extends State<VideosPage> {
  Future<PaginatedResponse<VideoResponse>> futureVideos = Future.value(
    PaginatedResponse<VideoResponse>.empty(),
  );

  VideoFields _sortBy = VideoFields.date;
  SortDirection _sortDirection = SortDirection.descending;

  Sortable<VideoFields> get _sortable =>
      Sortable<VideoFields>(field: _sortBy, direction: _sortDirection);

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
    _refreshVideos();
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
                DropdownButton<VideoFields>(
                  padding: const EdgeInsets.fromLTRB(12.0, 0.0, 12.0, 0.0),
                  value: _sortBy,
                  items: [
                    const DropdownMenuItem(
                      value: VideoFields.date,
                      child: Text("By date"),
                    ),
                    const DropdownMenuItem(
                      value: VideoFields.name,
                      child: Text("By name"),
                    ),
                    const DropdownMenuItem(
                      value: VideoFields.cameraID,
                      child: Text("By camera"),
                    ),
                  ],
                  underline: Container(),
                  icon: const Icon(Icons.sort),
                  onChanged: (value) {
                    setState(() {
                      _sortBy = value!;
                    });
                    _refreshVideos();
                  },
                ),
                IconButton(
                  onPressed: () {
                    setState(() {
                      _sortDirection = _sortDirection == SortDirection.ascending
                          ? SortDirection.descending
                          : SortDirection.ascending;
                    });
                    _refreshVideos();
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
                  onPressed: _refreshVideos,
                  icon: Icon(Icons.refresh),
                ),
              ],
            ),
          ],
        ),
        Expanded(
          child: FutureBuilder(
            future: futureVideos,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Center(child: Text(snapshot.error.toString()));
              }
              if (snapshot.hasData) {
                if (snapshot.data!.items.isEmpty) {
                  return const Center(child: Text("No videos found"));
                }
                return _buildVideoList(snapshot.data!.items);
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

  Widget _buildVideoList(List<VideoResponse> videos) {
    return ListView.separated(
      itemCount: videos.length,
      itemBuilder: (context, index) {
        return VideoTile(
          video: videos[index],
          downloadVideo: () async =>
              await widget.videoRepository.downloadVideo(videos[index].id),
          deleteVideo: () async {
            final result = await widget.videoRepository.deleteVideo(
              videos[index].id,
            );
            _refreshVideos();
            return result;
          },
        );
      },
      separatorBuilder: (context, index) => Divider(),
    );
  }

  // NOTE: This is meant to always be set to a future variable and not awaited
  Future<PaginatedResponse<VideoResponse>> _getAllVideos({
    int? page,
    int pageSize = 10,
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
      final query = VideoQuery(orderBy: _sortable);
      final response = await widget.videoRepository.getVideos(
        pagination: PaginationParams(pageIndex: page - 1, pageSize: pageSize),
        videoQuery: query,
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
      futureVideos = _getAllVideos();
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

  void _refreshVideos() {
    setState(() {
      futureVideos = _getAllVideos();
    });
  }
}
