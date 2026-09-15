"""
SubcriteriaScore — jedan red = jedan podkriterijum u okviru jednog SAR-a
(28 redova po kompletnom SAR-u). CLAUDE.md Sekcija 1, Nivo 1.

ARHITEKTONSKA ODLUKA (Database & Security agent, Faza 0): `institution_id`
je DENORMALIZOVAN ovde, iako se može dobiti JOIN-om na self_assessments.
Razlog: RLS politika nad ovom tabelom je prost kolonski uslov, ne
subquery u svakoj politici (subquery RLS se izvršava za SVAKI red).

Rizik denormalizacije (red sa institution_id koji NE odgovara SAR-u) je
zatvoren NA NIVOU BAZE, ne u servisnom sloju: kompozitni FK
(self_assessment_id, institution_id) -> self_assessments(id,
institution_id). Baza odbija nekonzistentan red bez obzira na bug u
aplikaciji.
"""

import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from caf.db.base import Base, TimestampMixin


class SubcriteriaScore(TimestampMixin, Base):
    __tablename__ = "subcriteria_scores"
    __table_args__ = (
        ForeignKeyConstraint(
            ["self_assessment_id", "institution_id"],
            ["self_assessments.id", "self_assessments.institution_id"],
            ondelete="CASCADE",
            name="fk_subcriteria_scores_sar_institution",
        ),
        CheckConstraint("score IS NULL OR (score >= 1 AND score <= 5)", name="ck_score_range"),
        CheckConstraint("input_lang IN ('me', 'en')", name="ck_input_lang_valid"),
        UniqueConstraint("self_assessment_id", "subcriteria_code", name="uq_sar_subcriteria_once"),
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
    subcriteria_code: Mapped[str] = mapped_column(
        String(4), ForeignKey("subcriteria.code", ondelete="RESTRICT"), nullable=False
    )

    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    weaknesses_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # CLAUDE.md Sekcija 6.1: korisnički unos se NE prevodi automatski —
    # čuva se jezik na kom je unesen.
    input_lang: Mapped[str] = mapped_column(
        String(2), nullable=False, default="me", server_default="me"
    )

    # Join ide preko kompozitnog FK-a (id + institution_id). Posljedica:
    # kad se score doda u `sar.subcriteria_scores`, ORM SAM popunjava i
    # self_assessment_id i institution_id iz roditelja — denormalizacija
    # se ne može "zaboraviti" u servisnom sloju.
    self_assessment: Mapped["SelfAssessment"] = relationship(  # noqa: F821
        back_populates="subcriteria_scores",
    )
