"""InstitutionService — `GET /institutions/me` (api-contract-v1.md, 3.1)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.exceptions import NotFoundError
from caf.core.i18n import Locale
from caf.core.security import TokenPayload
from caf.models import Institution, SelfAssessment, User
from caf.schemas.institution import InstitutionOut


class InstitutionService:
    def __init__(self, session: AsyncSession, user: TokenPayload, locale: Locale) -> None:
        self._session = session
        self._user = user
        self._locale = locale

    async def get_mine(self) -> InstitutionOut:
        # RLS već ograničava na sopstvenu instituciju — bez WHERE po id-u.
        institution = await self._session.scalar(select(Institution))
        if institution is None:
            # Ulogovan korisnik bez vidljive institucije = bug u RLS
            # kontekstu, ne normalan slučaj. 404 je najbezbjedniji odgovor.
            raise NotFoundError(locale=self._locale)

        members = await self._session.scalar(select(func.count()).select_from(User))
        sar_count = await self._session.scalar(select(func.count()).select_from(SelfAssessment))
        return InstitutionOut(
            id=institution.id,
            name_me=institution.name_me,
            name_en=institution.name_en,
            sag_members_count=members or 0,
            # 'caf_user' status dodjeljuje Nivo 2 (Faza 2). U Fazi 1:
            # null dok nema nijednog SAR-a, 'in_progress' čim proces krene.
            maturity_status="in_progress" if (sar_count or 0) > 0 else None,
        )
