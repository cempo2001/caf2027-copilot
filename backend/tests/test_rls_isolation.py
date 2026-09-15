"""
RLS tenant izolacija — KRITIČAN test (CLAUDE.md Sekcija 3, pravilo 6 i
Sekcija 7.2). `app_user` (runtime rola, bez BYPASSRLS) NIKAD ne vidi niti
mijenja podatke druge institucije, čak ni kad zna tačan UUID.

Priprema podataka ide kroz `admin_session` (superuser zaobilazi RLS po
definiciji); SVE provjere izolacije idu kroz `app_user_session`.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from tests.conftest import set_institution_context


async def _create_institution(session: AsyncSession, name: str) -> uuid.UUID:
    result = await session.execute(
        text("INSERT INTO institutions (name_me, name_en) VALUES (:n, :n) RETURNING id"),
        {"n": name},
    )
    institution_id = result.scalar_one()
    await session.commit()
    return institution_id


async def _create_self_assessment(session: AsyncSession, institution_id: uuid.UUID) -> uuid.UUID:
    result = await session.execute(
        text("INSERT INTO self_assessments (institution_id) VALUES (:iid) RETURNING id"),
        {"iid": str(institution_id)},
    )
    sar_id = result.scalar_one()
    await session.commit()
    return sar_id


async def test_app_user_sees_only_own_institution_self_assessments(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    institution_a = await _create_institution(admin_session, "Institucija A")
    institution_b = await _create_institution(admin_session, "Institucija B")
    sar_a = await _create_self_assessment(admin_session, institution_a)
    await _create_self_assessment(admin_session, institution_b)

    await set_institution_context(app_user_session, institution_a)
    result = await app_user_session.execute(text("SELECT id FROM self_assessments"))

    assert {row[0] for row in result.fetchall()} == {sar_a}, (
        "app_user sa kontekstom institucije A vidi tuđe SAR-ove — RLS izolacija narušena."
    )


async def test_app_user_cannot_read_other_institutions_sar_by_direct_id(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    institution_a = await _create_institution(admin_session, "Institucija C")
    institution_b = await _create_institution(admin_session, "Institucija D")
    sar_b = await _create_self_assessment(admin_session, institution_b)

    await set_institution_context(app_user_session, institution_a)
    result = await app_user_session.execute(
        text("SELECT id FROM self_assessments WHERE id = :sid"), {"sid": str(sar_b)}
    )

    assert result.fetchone() is None, "app_user je pročitao tuđi SAR direktno po ID-u."


async def test_app_user_cannot_update_other_institutions_sar(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    """Tuđi red je za UPDATE 'nevidljiv' — 0 pogođenih redova, bez greške.
    Servisni sloj to tumači kao 404 (ne otkriva postojanje tuđeg resursa)."""
    institution_a = await _create_institution(admin_session, "Institucija E")
    institution_b = await _create_institution(admin_session, "Institucija F")
    sar_b = await _create_self_assessment(admin_session, institution_b)

    await set_institution_context(app_user_session, institution_a)
    result = await app_user_session.execute(
        text("UPDATE self_assessments SET status = 'submitted' WHERE id = :sid"),
        {"sid": str(sar_b)},
    )
    await app_user_session.commit()
    assert result.rowcount == 0

    check = await admin_session.execute(
        text("SELECT status::text FROM self_assessments WHERE id = :sid"), {"sid": str(sar_b)}
    )
    assert check.scalar_one() == "draft"


async def test_app_user_cannot_insert_into_other_institution(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    institution_a = await _create_institution(admin_session, "Institucija G")
    institution_b = await _create_institution(admin_session, "Institucija H")

    await set_institution_context(app_user_session, institution_a)
    with pytest.raises(DBAPIError, match="row-level security"):
        await app_user_session.execute(
            text("INSERT INTO self_assessments (institution_id) VALUES (:iid)"),
            {"iid": str(institution_b)},
        )


async def test_app_user_without_context_sees_nothing(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    """Bez tenant konteksta: PRAZAN rezultat, nikad 'sve po defaultu'."""
    await _create_institution(admin_session, "Institucija I")

    result = await app_user_session.execute(text("SELECT id FROM institutions"))
    assert result.fetchall() == []


async def test_pooled_connection_after_context_reset_fails_closed(
    admin_session: AsyncSession, app_user_engine: AsyncEngine
) -> None:
    """
    Regresioni test za NULLIF u RLS politikama. Postgres poslije
    transakcije vraća postavljeni custom GUC na '' (ne NULL). Bez NULLIF
    bi `''::uuid` bacio grešku; ispravno ponašanje je prazan rezultat.
    Namjerno ISTA fizička konekcija kroz obje transakcije — tačno stanje
    konekcije vraćene u pool.
    """
    institution_a = await _create_institution(admin_session, "Institucija J")
    await _create_self_assessment(admin_session, institution_a)

    async with app_user_engine.connect() as conn:
        async with conn.begin():
            await conn.execute(
                text("SELECT set_config('app.current_institution_id', :iid, true)"),
                {"iid": str(institution_a)},
            )
            visible = await conn.execute(text("SELECT count(*) FROM self_assessments"))
            assert visible.scalar_one() >= 1

        async with conn.begin():
            leftover = await conn.execute(
                text("SELECT current_setting('app.current_institution_id', true)")
            )
            assert leftover.scalar_one() in ("", None)
            after_reset = await conn.execute(text("SELECT count(*) FROM self_assessments"))
            assert after_reset.scalar_one() == 0


async def test_app_user_cannot_modify_reference_subcriteria(
    app_user_session: AsyncSession,
) -> None:
    """Zvanični CAF okvir (subcriteria) je za aplikaciju samo za čitanje."""
    readable = await app_user_session.execute(text("SELECT count(*) FROM subcriteria"))
    assert readable.scalar_one() == 28

    with pytest.raises(DBAPIError, match="permission denied"):
        await app_user_session.execute(
            text("UPDATE subcriteria SET name_me = 'x' WHERE code = '1.1'")
        )
