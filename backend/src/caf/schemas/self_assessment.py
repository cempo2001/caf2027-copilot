"""Self-assessment (SAR) DTO — api-contract-v1.md, sekcija 4."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from caf.models.self_assessment import SarStatus
from caf.schemas.common import OrmModel

QualityFlag = Literal["ok", "too_short", "too_generic"]


class SarSummary(OrmModel):
    id: UUID
    status: SarStatus
    created_at: datetime
    approved_at: datetime | None = None


class SubcriteriaScoreOut(BaseModel):
    subcriteria_code: str
    criterion_number: int
    name_me: str | None
    name_en: str | None
    score: int | None
    evidence_text: str | None
    weaknesses_text: str | None
    input_lang: str
    quality_flag: QualityFlag | None


class SarDetail(BaseModel):
    id: UUID
    status: SarStatus
    approved_at: datetime | None
    approved_by: UUID | None
    subcriteria_scores: list[SubcriteriaScoreOut]


class SubcriteriaScoreUpdate(BaseModel):
    """
    PATCH tijelo za Guided Wizard korak. Sva polja opciona — korisnik
    može sačuvati samo tekst pa kasnije ocjenu. Prazan string se
    normalizuje u None da 'obrisano' i 'nikad uneseno' znače isto.
    """

    evidence_text: str | None = Field(default=None, max_length=20_000)
    weaknesses_text: str | None = Field(default=None, max_length=20_000)
    score: int | None = Field(default=None, ge=1, le=5)

    def model_post_init(self, __context: object) -> None:
        if self.evidence_text is not None and not self.evidence_text.strip():
            self.evidence_text = None
        if self.weaknesses_text is not None and not self.weaknesses_text.strip():
            self.weaknesses_text = None


class ApproveResponse(OrmModel):
    id: UUID
    status: SarStatus
    approved_at: datetime
    approved_by: UUID
