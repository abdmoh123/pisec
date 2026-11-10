"""Paginated model class that query params inherit."""

from collections.abc import Iterable
from typing import Annotated, TypeVar

from pydantic import BaseModel, Field


class PaginatedParams(BaseModel):
    """Re-usable model for pagination.

    Also includes some validation.
    """

    page_index: Annotated[int, Field(default=0, ge=0)]
    page_size: Annotated[int, Field(default=100, ge=1)]


T = TypeVar("T", bound=BaseModel)


class PaginatedResponse[T: BaseModel](BaseModel):
    """Re-usable model for returning paginated results."""

    items: Annotated[list[T], Field()]
    page_index: Annotated[int, Field(ge=0)]
    page_size: Annotated[int, Field(ge=1)]
    total_items: Annotated[int, Field(ge=0)]
    total_pages: Annotated[int, Field(ge=0)]

    @classmethod
    def create(cls, items: Iterable[T], page_index: int, page_size: int, total_items: int) -> PaginatedResponse[T]:
        """Creates a paginated response and auto-generates the total pages."""
        # Ceiling division
        total_pages: int = (total_items + page_size - 1) // page_size
        return cls(
            items=list(items),
            page_index=page_index,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )
