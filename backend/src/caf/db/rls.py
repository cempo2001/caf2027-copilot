"""
Row Level Security — tenant kontekst po sesiji.

Database & Security Agent (CLAUDE.md 7.2). Most između JWT claim-a
`institution_id` i RLS politika (migracija 0001), koje čitaju
`NULLIF(current_setting('app.current_institution_id', true), '')::uuid`.

Kontekst se postavlja sa `is_local=true` — važi SAMO za tekuću
transakciju i nestaje na commit/rollback. To je namjerno (konekcija
vraćena u pool ne smije ponijeti tuđi tenant), ali znači da se mora
ponovo postaviti na početku svake transakcije. `bind_tenant_context`
to rješava jednom, na nivou sesije, kroz SQLAlchemy `after_begin` event.
"""

from uuid import UUID

from sqlalchemy import event, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, SessionTransaction

_SET_CONTEXT = text("SELECT set_config('app.current_institution_id', :institution_id, true)")


async def set_tenant_context(session: AsyncSession, institution_id: UUID) -> None:
    """Jednokratno postavljanje za TEKUĆU transakciju (testovi, skripte)."""
    await session.execute(_SET_CONTEXT, {"institution_id": str(institution_id)})


def bind_tenant_context(session: AsyncSession, institution_id: UUID) -> None:
    """
    Vezuje instituciju za cijeli životni vijek sesije: na početku SVAKE
    transakcije (uključujući one poslije commit-a) izvršava set_config na
    toj konekciji. Koristi se iz api/deps.py za request-scoped sesije.
    """
    institution = str(institution_id)

    def _on_begin(_: Session, __: SessionTransaction, connection: Connection) -> None:
        connection.execute(_SET_CONTEXT, {"institution_id": institution})

    event.listen(session.sync_session, "after_begin", _on_begin)


async def set_national_context(session: AsyncSession) -> None:
    """
    Nivo 2 / sistemski pristup (Faza 2): eksplicitno prazan kontekst.
    Politike iz 0001 to tumače kao "ništa" (fail-closed) — Nivo 2
    agregacija zahtijeva posebnu ADR i posebne politike, ne ovaj poziv.
    """
    await session.execute(text("SELECT set_config('app.current_institution_id', '', true)"))
