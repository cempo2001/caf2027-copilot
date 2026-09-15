"""
SelfAssessment (SAR) — CLAUDE.md Sekcija 1, Nivo 1.

Approved Lock (CLAUDE.md Sekcija 3, pravilo 3) se primjenjuje na nivou
baze preko triggera `check_approved_sar_lock` (migracija 0001) — ovaj
model ne implementira lock logiku, samo definiše šemu koju trigger štiti.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from caf.db.base import Base, TimestampMixin


class SarStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"


class SelfAssessment(TimestampMixin, Base):
    __tablename__ = "self_assessments"
    __table_args__ = (
        # Meta za kompozitni FK iz subcriteria_scores — garantuje na nivou
        # baze da denormalizovani institution_id djeteta odgovara SAR-u.
        UniqueConstraint("id", "institution_id", name="uq_self_assessments_id_institution"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[SarStatus] = mapped_column(
        SAEnum(
            SarStatus,
            name="sar_status",
            native_enum=True,
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=SarStatus.DRAFT,
        server_default=SarStatus.DRAFT.value,
    )

    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )

    institution: Mapped["Institution"] = relationship(  # noqa: F821
        back_populates="self_assessments"
    )
    subcriteria_scores: Mapped[list["SubcriteriaScore"]] = relationship(  # noqa: F821
        back_populates="self_assessment",
        cascade="all, delete-orphan",
    )
