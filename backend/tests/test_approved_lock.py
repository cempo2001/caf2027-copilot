"""
Approved Lock — KRITIČAN test (CLAUDE.md Sekcija 1: "trajno zaključavanje
odobrenog SAR-a na nivou baze podataka"; Sekcija 3 pravilo 3: HTTP 409).

Testira trigger `check_approved_sar_lock` (migracija 0001) — NE servisni
sloj (dolazi u Koraku 5). Namjerno: trigger je zadnja linija odbrane i
mora raditi nezavisno od bugova u aplikaciji.

Sve operacije idu kroz `app_user_session` (stvarni put aplikacije). Tenant
kontekst je transakcijski, pa se postavlja na početku svake transakcije.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import set_institution_context


async def _create_institution(admin_session: AsyncSession, name: str) -> uuid.UUID:
    result = await admin_session.execute(
        text("INSERT INTO institutions (name_me, name_en) VALUES (:n, :n) RETURNING id"),
        {"n": name},
    )
    institution_id = result.scalar_one()
    await admin_session.commit()
    return institution_id


async def _setup_approved_sar(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> tuple[uuid.UUID, uuid.UUID]:
    """Institucija + draft SAR + jedan score (1.1), pa odobravanje SAR-a.
    Vraća (institution_id, sar_id)."""
    institution_id = await _create_institution(admin_session, "Lock test")

    # Transakcija 1: SAR + score
    await set_institution_context(app_user_session, institution_id)
    result = await app_user_session.execute(
        text(
            "INSERT INTO self_assessments (institution_id, status) "
            "VALUES (:iid, 'draft') RETURNING id"
        ),
        {"iid": str(institution_id)},
    )
    sar_id = result.scalar_one()
    await app_user_session.execute(
        text(
            "INSERT INTO subcriteria_scores "
            "(self_assessment_id, institution_id, subcriteria_code, score, input_lang) "
            "VALUES (:sar, :iid, '1.1', 3, 'me')"
        ),
        {"sar": str(sar_id), "iid": str(institution_id)},
    )
    await app_user_session.commit()

    # Transakcija 2: draft -> approved (DOZVOLJEN prelaz)
    await set_institution_context(app_user_session, institution_id)
    await app_user_session.execute(
        text(
            "UPDATE self_assessments SET status = 'approved', approved_at = now() "
            "WHERE id = :sar"
        ),
        {"sar": str(sar_id)},
    )
    await app_user_session.commit()

    # Transakcija 3 (otvorena za test): kontekst spreman
    await set_institution_context(app_user_session, institution_id)
    return institution_id, sar_id


async def test_draft_to_approved_transition_is_allowed(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    """Kontrola: trigger NE smije blokirati sam čin odobravanja."""
    _, sar_id = await _setup_approved_sar(admin_session, app_user_session)

    result = await admin_session.execute(
        text("SELECT status::text FROM self_assessments WHERE id = :sar"), {"sar": str(sar_id)}
    )
    assert result.scalar_one() == "approved"


async def test_cannot_update_approved_self_assessment(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    _, sar_id = await _setup_approved_sar(admin_session, app_user_session)

    with pytest.raises(DBAPIError, match="sar_locked"):
        await app_user_session.execute(
            text("UPDATE self_assessments SET status = 'draft' WHERE id = :sar"),
            {"sar": str(sar_id)},
        )


async def test_cannot_delete_approved_self_assessment(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    _, sar_id = await _setup_approved_sar(admin_session, app_user_session)

    with pytest.raises(DBAPIError, match="sar_locked"):
        await app_user_session.execute(
            text("DELETE FROM self_assessments WHERE id = :sar"), {"sar": str(sar_id)}
        )


async def test_cannot_update_subcriteria_score_after_approval(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    _, sar_id = await _setup_approved_sar(admin_session, app_user_session)

    with pytest.raises(DBAPIError, match="sar_locked"):
        await app_user_session.execute(
            text(
                "UPDATE subcriteria_scores SET score = 5 "
                "WHERE self_assessment_id = :sar AND subcriteria_code = '1.1'"
            ),
            {"sar": str(sar_id)},
        )


async def test_cannot_insert_subcriteria_score_after_approval(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    institution_id, sar_id = await _setup_approved_sar(admin_session, app_user_session)

    with pytest.raises(DBAPIError, match="sar_locked"):
        await app_user_session.execute(
            text(
                "INSERT INTO subcriteria_scores "
                "(self_assessment_id, institution_id, subcriteria_code, score, input_lang) "
                "VALUES (:sar, :iid, '1.2', 4, 'me')"
            ),
            {"sar": str(sar_id), "iid": str(institution_id)},
        )


async def test_cannot_delete_subcriteria_score_after_approval(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    _, sar_id = await _setup_approved_sar(admin_session, app_user_session)

    with pytest.raises(DBAPIError, match="sar_locked"):
        await app_user_session.execute(
            text(
                "DELETE FROM subcriteria_scores "
                "WHERE self_assessment_id = :sar AND subcriteria_code = '1.1'"
            ),
            {"sar": str(sar_id)},
        )


async def test_lock_holds_even_for_superuser(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    """
    Trigger nije RLS — važi i za superuser-a/migracionu rolu. Odobren SAR
    ne može izmijeniti ni neko sa punim pristupom bazi kroz običan UPDATE
    (za namjernu administrativnu izmjenu bi morao eksplicitno isključiti
    trigger, što je vidljiva i revizibilna radnja).
    """
    _, sar_id = await _setup_approved_sar(admin_session, app_user_session)

    with pytest.raises(DBAPIError, match="sar_locked"):
        await admin_session.execute(
            text("UPDATE self_assessments SET status = 'submitted' WHERE id = :sar"),
            {"sar": str(sar_id)},
        )


async def test_score_cannot_claim_foreign_institution(
    admin_session: AsyncSession, app_user_session: AsyncSession
) -> None:
    """
    Kompozitni FK (self_assessment_id, institution_id): red koji tvrdi da
    pripada instituciji A, a veže se za SAR institucije B, baza odbija —
    denormalizovani institution_id ne može "pobjeći" od roditelja.
    Pokrenuto kao superuser namjerno: dokazujemo da garancija NE zavisi od
    RLS-a, nego od same šeme.
    """
    institution_a = await _create_institution(admin_session, "FK A")
    institution_b = await _create_institution(admin_session, "FK B")

    result = await admin_session.execute(
        text(
            "INSERT INTO self_assessments (institution_id) VALUES (:iid) RETURNING id"
        ),
        {"iid": str(institution_b)},
    )
    sar_b = result.scalar_one()
    await admin_session.commit()

    with pytest.raises(IntegrityError):
        await admin_session.execute(
            text(
                "INSERT INTO subcriteria_scores "
                "(self_assessment_id, institution_id, subcriteria_code, input_lang) "
                "VALUES (:sar, :iid, '1.1', 'me')"
            ),
            {"sar": str(sar_b), "iid": str(institution_a)},
        )
