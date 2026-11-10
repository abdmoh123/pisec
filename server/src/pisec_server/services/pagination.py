"""Service functions relating to pagination."""

from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from pisec_server.api.models.paginated.generic import PaginatedParams, PaginatedResponse

T = TypeVar("T", bound=BaseModel)
M = TypeVar("M")


def paginate[M, T: BaseModel](
    db: Session, query: Select[M], params: PaginatedParams, to_response: Callable[[M], T]
) -> PaginatedResponse[T]:
    """Runs a given select query and wraps it in a paginated response."""
    count_query = select(func.count()).select_from(query.subquery())
    total_items = db.scalar(count_query) or 0

    skip = params.page_index * params.page_size
    items: list[M] = list(db.execute(query.offset(skip).limit(params.page_size)).scalars().all())

    item_responses: list[T] = [to_response(item) for item in items]

    return PaginatedResponse[T].create(item_responses, params.page_index, params.page_size, total_items)
