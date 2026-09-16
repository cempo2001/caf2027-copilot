"""CIP akcioni plan DTO — api-contract-v1.md, sekcija 5."""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from caf.models.cip_item import CipQuadrant, CipStatus
from caf.schemas.common import OrmModel


class CipItemOut(OrmModel):
    id: UUID
    title_me: str
    title_en: str
    quadrant: CipQuadrant
    as_is: str
    to_be: str
    status: CipStatus


class CipListOut(BaseModel):
    """5.1 — bez paginacije (akcioni plan jednog SAR-a je mali skup)."""

    items: list[CipItemOut]


class CipItemCreate(BaseModel):
    title_me: str = Field(min_length=1, max_length=300)
    title_en: str = Field(min_length=1, max_length=300)
    quadrant: CipQuadrant
    as_is: str = Field(min_length=1, max_length=5_000)
    to_be: str = Field(min_length=1, max_length=5_000)

    @field_validator("title_me", "title_en", "as_is", "to_be")
    @classmethod
    def _strip_and_require(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped
