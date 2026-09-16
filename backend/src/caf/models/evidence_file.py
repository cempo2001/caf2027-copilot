"""
EvidenceFile — metapodaci dokaza uz podkriterijum (api-contract-v1.md 6.1).

Vault & Documents Agent (CLAUDE.md 7.6). Sam sadržaj fajla je u MinIO
(`object_key`), ovdje su samo metapodaci. Red postoji isključivo za fajl
koji je prošao SHA-256 i AV korak — `infected` nije dozvoljena vrijednost
ni na nivou baze (CHECK u migraciji 0004).
"""

import uuid
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, ForeignKeyConstraint, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from caf.db.base import Base, TimestampMixin


class StoredAvStatus(StrEnum):
    CLEAN = "clean"
    # Samo lokalni razvoj sa AV_SCAN_MODE=disabled — NIJE verifikovan dokaz.
    PENDING = "pending"


class EvidenceFile(TimestampMixin, Base):
    __tablename__ = "evidence_files"
    __table_args__ = (
        ForeignKeyConstraint(
            ["self_assessment_id", "institution_id"],
            ["self_assessments.id", "self_assessments.institution_id"],
            ondelete="CASCADE",
            name="fk_evidence_files_sar_institution",
        ),
        CheckConstraint(
            "av_scan_status IN ('clean', 'pending')", name="ck_evidence_files_av_status"
        ),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_evidence_files_sha256"),
        CheckConstraint("size_bytes > 0", name="ck_evidence_files_size"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    self_assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    subcriteria_code: Mapped[str] = mapped_column(
        String(4), ForeignKey("subcriteria.code", ondelete="RESTRICT"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(127), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    av_scan_status: Mapped[str] = mapped_column(String(16), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
