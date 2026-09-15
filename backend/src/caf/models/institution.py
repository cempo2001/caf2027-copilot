"""
Institution — Nivo 1 tenant (CLAUDE.md Sekcija 1).

Vrh tenant hijerarhije: svaki `institution_id` u ostalim tabelama
referencira ovaj model. RLS politika ovde je najjednostavnija moguća —
korisnik vidi SAMO svoj red (vidi migraciju 0001, CREATE POLICY).
"""

import uuid

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from caf.db.base import Base, TimestampMixin


class Institution(TimestampMixin, Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Statički dvojezični sadržaj — CLAUDE.md Sekcija 6.2 (Database agent
    # odluka: parovi _me/_en za sadržaj koji institucija ne mijenja često,
    # za razliku od korisničkog unosa koji nosi jezik-tag, vidi
    # SubcriteriaScore.input_lang).
    name_me: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="institution")  # noqa: F821
    self_assessments: Mapped[list["SelfAssessment"]] = relationship(  # noqa: F821
        back_populates="institution"
    )
