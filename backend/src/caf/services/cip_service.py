"""
CipService — akcioni plan poboljšanja (api-contract-v1.md 5).

Backend Agent (CLAUDE.md 7.3). Sesija je već tenant-scoped (api/deps.py);
servis nikad ne filtrira po institution_id ručno. Upis poslije Approved
Lock-a vraća 409 (sloj 1 u `SarAccess`, sloj 2 trigger iz migracije 0004).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.i18n import Locale
from caf.core.security import TokenPayload
from caf.models import CipItem, CipStatus
from caf.schemas.cip import CipItemCreate, CipItemOut, CipListOut
from caf.services.sar_access import EDITOR_ROLES, SarAccess


class CipService:
    def __init__(self, session: AsyncSession, user: TokenPayload, locale: Locale) -> None:
        self._session = session
        self._user = user
        self._locale = locale
        self._access = SarAccess(session, user, locale)

    async def list_items(self, sar_id: UUID) -> CipListOut:
        sar = await self._access.load_sar(sar_id)
        result = await self._session.execute(
            select(CipItem)
            .where(CipItem.self_assessment_id == sar.id)
            .order_by(CipItem.created_at, CipItem.id)
        )
        return CipListOut(items=[CipItemOut.model_validate(item) for item in result.scalars()])

    async def create_item(self, sar_id: UUID, payload: CipItemCreate) -> CipItemOut:
        self._access.require_role(EDITOR_ROLES)
        sar = await self._access.load_unlocked_sar(sar_id)

        item = CipItem(
            self_assessment_id=sar.id,
            institution_id=sar.institution_id,
            title_me=payload.title_me,
            title_en=payload.title_en,
            quadrant=payload.quadrant,
            as_is=payload.as_is,
            to_be=payload.to_be,
            status=CipStatus.PLANNED,
            input_lang=self._locale,
            created_by=self._user.sub,
        )
        self._session.add(item)
        await self._access.commit_or_map_lock()
        await self._session.refresh(item)
        return CipItemOut.model_validate(item)
