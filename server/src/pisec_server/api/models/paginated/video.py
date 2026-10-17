"""Query parameters for paginated video responses."""

from typing import Annotated

from fastapi import Query

from pisec_server.api.models.paginated.generic import PaginatedParams
from pisec_server.api.models.sortable import Sortable, SortableParser
from pisec_server.api.models.types.video_columns import VideoColumns
from pisec_server.core.validation.regex import file_name_regex


class VideoGetParams(PaginatedParams):
    """Video GET query parameters with pagination."""

    video_id: Annotated[list[int] | None, Query(ge=1)] = None  # Named in singular form due to how it's queried
    camera_id: Annotated[list[int] | None, Query(ge=1)] = None  # Named in singular form due to how it's queried
    file_name: Annotated[str | None, Query(pattern=file_name_regex, min_length=5)] = None
    order_by: Annotated[Sortable[VideoColumns], SortableParser(VideoColumns), Query()] = Sortable(
        VideoColumns.ID, ascending=True
    )
