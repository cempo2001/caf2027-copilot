"""
CipItem — stavka akcionog plana poboljšanja (CIP), 2x2 matrica
(api-contract-v1.md 5; CLAUDE.md Sekcija 1, Nivo 1).

Isti obrazac kao `SubcriteriaScore` (ADR-0001): denormalizovan
`institution_id` + kompozitni FK na self_assessments(id, institution_id),
RLS i Approved Lock trigger dolaze iz migracije 0004.
"""

import uuid
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, String, Text, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from caf.db.base import Base, TimestampMixin


class CipQuadrant(StrEnum):
    QUICK_WIN = "quick_win"
    STRATEGIC = "strategic"
    FILL_IN = "fill_in"
    RECONSIDER = "reconsider"


class CipStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"


def _enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]


class CipItem(TimestampMixin, Base):
    __tablename__ = "cip_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["self_assessment_id", "institution_id"],
            ["self_assessments.id", "self_assessments.institution_id"],
            ondelete="CASCADE",
            name="fk_cip_items_sar_institution",
        ),
        CheckConstraint("input_lang IN ('me', 'en')", name="ck_cip_items_input_lang"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    self_assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    title_me: Mapped[str] = mapped_column(String(300), nullable=False)
    title_en: Mapped[str] = mapped_column(String(300), nullable=False)
    quadrant: Mapped[CipQuadrant] = mapped_column(
        SAEnum(
            CipQuadrant,
            name="cip_quadrant",
            native_enum=True,
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    as_is: Mapped[str] = mapped_column(Text, nullable=False)
    to_be: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CipStatus] = mapped_column(
        SAEnum(
            CipStatus,
            name="cip_status",
            native_enum=True,
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=CipStatus.PLANNED,
        server_default=CipStatus.PLANNED.value,
    )
    # CLAUDE.md 6.1 — slobodan tekst se ne prevodi, pamti se jezik unosa.
    input_lang: Mapped[str] = mapped_column(
        String(2), nullable=False, default="me", server_default="me"
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
