"""
SarService — životni ciklus samoprocjene (SAR) unutar jedne institucije.

Backend Agent (CLAUDE.md 7.3), Approved Lock dio na Opus-nivou pažnje.
Servis pretpostavlja da je sesija VEĆ tenant-scoped (api/deps.py je
postavio RLS kontekst) — zato nikad ne filtrira po institution_id
ručno; RLS to garantuje, a `institution_id` iz tokena koristi samo pri
UPISU (denormalizacija u subcriteria_scores).

Dva sloja odbrane za Approved Lock (Sekcija 3, pravilo 3):
1. Servis provjeri status i vrati čist 409 PRIJE upita (primarno).
2. Ako ipak nešto prođe (race, bug), trigger `check_approved_sar_lock`
   podigne 'sar_locked' — servis ga prepozna i mapira na isti 409.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from caf.core.exceptions import (
    InsufficientRoleError,
    NotFoundError,
    SarIncompleteError,
    SarLockedError,
    UnknownSubcriteriaError,
)
from caf.core.i18n import Locale
from caf.core.security import Role, TokenPayload
from caf.models import SarStatus, SelfAssessment, Subcriteria, SubcriteriaScore
from caf.schemas.common import Page
from caf.schemas.self_assessment import (
    ApproveResponse,
    QualityFlag,
    SarDetail,
    SarSummary,
    SubcriteriaScoreOut,
    SubcriteriaScoreUpdate,
)

EXPECTED_SUBCRITERIA_COUNT = 28
# Ispod ovog broja riječi unos je "prekratak" — prag je početna
# vrijednost za oba jezika; Sekcija 6.1 traži da se pravila za me/en
# razdvoje čim UX istraživanje (Frontend agent) da stvarne brojke.
MIN_WORDS_FOR_QUALITY = 20

_CAN_MANAGE_SAR = {Role.SPONSOR, Role.CAF_LEAD}
_CAN_EDIT_SCORES = {Role.SPONSOR, Role.CAF_LEAD, Role.CAE_TEAM_MEMBER}


def _is_sar_locked_error(exc: DBAPIError) -> bool:
    return "sar_locked" in str(exc.orig or exc)


def _quality_flag(evidence: str | None, weaknesses: str | None) -> QualityFlag | None:
    if evidence is None and weaknesses is None:
        return None
    words = len((evidence or "").split()) + len((weaknesses or "").split())
    if words < MIN_WORDS_FOR_QUALITY:
        return "too_short"
    return "ok"


class SarService:
    def __init__(self, session: AsyncSession, user: TokenPayload, locale: Locale) -> None:
        self._session = session
        self._user = user
        self._locale = locale

    # ------------------------------------------------------------------ #
    # Čitanje
    # ------------------------------------------------------------------ #
    async def list_self_assessments(self, *, page: int = 1, page_size: int = 20) -> Page[SarSummary]:
        total = await self._session.scalar(select(func.count()).select_from(SelfAssessment))
        result = await self._session.execute(
            select(SelfAssessment)
            .order_by(SelfAssessment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [SarSummary.model_validate(sar) for sar in result.scalars()]
        return Page(items=items, total=total or 0, page=page, page_size=page_size)

    async def get_detail(self, sar_id: UUID) -> SarDetail:
        sar = await self._get_or_404(sar_id, with_scores=True)
        return await self._to_detail(sar)

    # ------------------------------------------------------------------ #
    # Pisanje
    # ------------------------------------------------------------------ #
    async def create_self_assessment(self) -> SarSummary:
        self._require_role(_CAN_MANAGE_SAR)
        sar = SelfAssessment(institution_id=self._user.institution_id)
        self._session.add(sar)
        await self._session.commit()
        await self._session.refresh(sar)
        return SarSummary.model_validate(sar)

    async def update_subcriteria(
        self, sar_id: UUID, code: str, payload: SubcriteriaScoreUpdate
    ) -> SubcriteriaScoreOut:
        self._require_role(_CAN_EDIT_SCORES)
        sar = await self._get_or_404(sar_id)
        self._raise_if_locked(sar)  # sloj 1: čist 409 prije upita

        subcriteria = await self._session.get(Subcriteria, code)
        if subcriteria is None:
            raise UnknownSubcriteriaError(locale=self._locale)

        score = await self._session.scalar(
            select(SubcriteriaScore).where(
                SubcriteriaScore.self_assessment_id == sar.id,
                SubcriteriaScore.subcriteria_code == code,
            )
        )
        if score is None:
            score = SubcriteriaScore(
                self_assessment_id=sar.id,
                institution_id=sar.institution_id,
                subcriteria_code=code,
            )
            self._session.add(score)

        fields = payload.model_dump(exclude_unset=True)
        for name, value in fields.items():
            setattr(score, name, value)
        if "evidence_text" in fields or "weaknesses_text" in fields:
            score.input_lang = self._locale  # Sekcija 6.1: jezik unosa se pamti

        try:
            await self._session.commit()
        except DBAPIError as exc:  # sloj 2: trigger kao zadnja linija odbrane
            await self._session.rollback()
            if _is_sar_locked_error(exc):
                raise SarLockedError(locale=self._locale) from exc
            raise
        await self._session.refresh(score)
        return self._to_score_out(score, subcriteria)

    async def approve(self, sar_id: UUID) -> ApproveResponse:
        """
        Approved Lock. Samo Sponsor. Zahtijeva svih 28 ocijenjenih
        podkriterijuma. Nepovratno — drugi poziv vraća 409, ne no-op
        (api-contract-v1.md 4.6: jasno ko je i kada ZAISTA odobrio).
        """
        self._require_role({Role.SPONSOR})
        sar = await self._get_or_404(sar_id)
        self._raise_if_locked(sar)

        scored = await self._session.scalar(
            select(func.count())
            .select_from(SubcriteriaScore)
            .where(
                SubcriteriaScore.self_assessment_id == sar.id,
                SubcriteriaScore.score.is_not(None),
            )
        )
        if (scored or 0) < EXPECTED_SUBCRITERIA_COUNT:
            raise SarIncompleteError(locale=self._locale)

        sar.status = SarStatus.APPROVED
        sar.approved_at = datetime.now(timezone.utc)
        sar.approved_by = self._user.sub
        try:
            await self._session.commit()
        except DBAPIError as exc:
            await self._session.rollback()
            if _is_sar_locked_error(exc):
                raise SarLockedError(locale=self._locale) from exc
            raise
        await self._session.refresh(sar)
        return ApproveResponse.model_validate(sar)

    # ------------------------------------------------------------------ #
    # Interno
    # ------------------------------------------------------------------ #
    def _require_role(self, allowed: set[Role]) -> None:
        if self._user.role not in allowed:
            raise InsufficientRoleError(locale=self._locale)

    def _raise_if_locked(self, sar: SelfAssessment) -> None:
        if sar.status == SarStatus.APPROVED:
            raise SarLockedError(locale=self._locale)

    async def _get_or_404(self, sar_id: UUID, *, with_scores: bool = False) -> SelfAssessment:
        stmt = select(SelfAssessment).where(SelfAssessment.id == sar_id)
        if with_scores:
            stmt = stmt.options(selectinload(SelfAssessment.subcriteria_scores))
        sar = await self._session.scalar(stmt)
        if sar is None:
            # Ne postoji ILI pripada drugoj instituciji (RLS) — isti odgovor.
            raise NotFoundError(locale=self._locale)
        return sar

    async def _to_detail(self, sar: SelfAssessment) -> SarDetail:
        subcriteria = (
            await self._session.execute(select(Subcriteria).order_by(Subcriteria.display_order))
        ).scalars().all()
        by_code = {s.subcriteria_code: s for s in sar.subcriteria_scores}
        scores = [self._to_score_out(by_code.get(sc.code), sc) for sc in subcriteria]
        return SarDetail(
            id=sar.id,
            status=sar.status,
            approved_at=sar.approved_at,
            approved_by=sar.approved_by,
            subcriteria_scores=scores,
        )

    @staticmethod
    def _to_score_out(
        score: SubcriteriaScore | None, subcriteria: Subcriteria
    ) -> SubcriteriaScoreOut:
        """Svih 28 podkriterijuma je uvijek u odgovoru — neocijenjeni kao prazni
        redovi, da Guided Wizard ne mora da 'pogađa' koji nedostaju."""
        return SubcriteriaScoreOut(
            subcriteria_code=subcriteria.code,
            criterion_number=subcriteria.criterion_number,
            name_me=subcriteria.name_me,
            name_en=subcriteria.name_en,
            score=score.score if score else None,
            evidence_text=score.evidence_text if score else None,
            weaknesses_text=score.weaknesses_text if score else None,
            input_lang=score.input_lang if score else "me",
            quality_flag=_quality_flag(
                score.evidence_text if score else None,
                score.weaknesses_text if score else None,
            ),
        )
