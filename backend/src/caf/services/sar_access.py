"""
Zajednička pravila pristupa roditeljskom SAR-u za module Faze 1
(CIP, dokazi, konsenzus) — jedno mjesto umjesto kopiranja u svaki servis.

Isti dvoslojni obrazac kao `SarService` (ADR-0001):
1. `load_unlocked_sar` vraća čist 409 PRIJE bilo kakvog upisa;
2. `commit_or_map_lock` hvata `sar_locked` iz triggera (race / bug) i
   mapira ga na isti 409.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.exceptions import (
    InsufficientRoleError,
    NotFoundError,
    SarLockedError,
    UnknownSubcriteriaError,
)
from caf.core.i18n import Locale
from caf.core.security import Role, TokenPayload
from caf.models import SarStatus, SelfAssessment, Subcriteria

# Uloge koje unose sadržaj samoprocjene (ocjene, CIP, dokazi). Employee je
# read-only. Mora ostati usklađeno sa `sar_service._CAN_EDIT_SCORES`.
EDITOR_ROLES: frozenset[Role] = frozenset({Role.SPONSOR, Role.CAF_LEAD, Role.CAE_TEAM_MEMBER})


def is_sar_locked_error(exc: DBAPIError) -> bool:
    return "sar_locked" in str(exc.orig or exc)


class SarAccess:
    def __init__(self, session: AsyncSession, user: TokenPayload, locale: Locale) -> None:
        self._session = session
        self._user = user
        self._locale = locale

    def require_role(self, allowed: frozenset[Role]) -> None:
        if self._user.role not in allowed:
            raise InsufficientRoleError(locale=self._locale)

    async def load_sar(self, sar_id: UUID) -> SelfAssessment:
        sar = await self._session.scalar(select(SelfAssessment).where(SelfAssessment.id == sar_id))
        if sar is None:
            # Ne postoji ILI pripada drugoj instituciji (RLS) — isti odgovor.
            raise NotFoundError(locale=self._locale)
        return sar

    async def load_unlocked_sar(self, sar_id: UUID) -> SelfAssessment:
        sar = await self.load_sar(sar_id)
        if sar.status == SarStatus.APPROVED:
            raise SarLockedError(locale=self._locale)
        return sar

    async def load_subcriteria(self, code: str) -> Subcriteria:
        subcriteria = await self._session.get(Subcriteria, code)
        if subcriteria is None:
            raise UnknownSubcriteriaError(locale=self._locale)
        return subcriteria

    async def commit_or_map_lock(self) -> None:
        try:
            await self._session.commit()
        except DBAPIError as exc:
            await self._session.rollback()
            if is_sar_locked_error(exc):
                raise SarLockedError(locale=self._locale) from exc
            raise
