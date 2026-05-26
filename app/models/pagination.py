from typing import Generic, TypeVar
from pydantic import BaseModel, computed_field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.per_page == 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page

    @computed_field
    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages


class Page(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta
