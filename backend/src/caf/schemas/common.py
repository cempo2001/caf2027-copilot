"""Zajedničke DTO šeme — error format i paginacija (api-contract-v1.md, 1.2/1.4)."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standardan format greške: stabilan ključ + lokalizovana poruka."""

    error: str = Field(examples=["sar_locked"])
    message: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20


class OrmModel(BaseModel):
    """Bazna klasa za response šeme koje se pune iz ORM objekata."""

    model_config = ConfigDict(from_attributes=True)
