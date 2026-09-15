"""
API tok Faze 0 kroz HTTP (httpx + ASGI), protiv testcontainers baze sa
migracijama 0001+0002, kao `app_user` — isti put kao produkcija.

Pokriva (api-contract-v1.md): login (2.1), institutions/me (3.1), SAR
lista/kreiranje/detalj (4.1–4.3), izmjena podkriterijuma (4.4), approve
(4.6), i format greške (1.2) NA OBA JEZIKA (CLAUDE.md 6.3 — modul nije
gotov ako radi samo na jednom jeziku).
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from caf.core.config import Settings, get_settings
from caf.core.i18n import translate
from caf.core.passwords import hash_password
from caf.db.session import create_session_factory, get_db_session
from caf.main import create_app
from tests.conftest import _settings_for

PASSWORD = "Tajna-Lozinka-2027!"


# ---------------------------------------------------------------------- #
# Fixtures
# ---------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def api_settings(app_user_engine: AsyncEngine) -> Settings:
    return _settings_for(str(app_user_engine.url.render_as_string(hide_password=False)))


@pytest_asyncio.fixture
async def client(app_user_engine: AsyncEngine, api_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    factory = create_session_factory(app_user_engine)

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_settings] = lambda: api_settings

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


class Seed:
    def __init__(self, institution_id: uuid.UUID, suffix: str) -> None:
        self.institution_id = institution_id
        self.sponsor = f"sponsor-{suffix}@test.me"
        self.caf_lead = f"lead-{suffix}@test.me"
        self.employee = f"employee-{suffix}@test.me"


@pytest_asyncio.fixture
async def seed(admin_session: AsyncSession) -> Seed:
    """Institucija sa tri korisnika (sponsor, caf_lead, employee)."""
    suffix = uuid.uuid4().hex[:8]
    institution_id = (
        await admin_session.execute(
            text("INSERT INTO institutions (name_me, name_en) VALUES (:me, :en) RETURNING id"),
            {"me": f"Ministarstvo {suffix}", "en": f"Ministry {suffix}"},
        )
    ).scalar_one()
    s = Seed(institution_id, suffix)
    hashed = hash_password(PASSWORD)
    for email, role in ((s.sponsor, "sponsor"), (s.caf_lead, "caf_lead"), (s.employee, "employee")):
        await admin_session.execute(
            text(
                "INSERT INTO users (institution_id, email, hashed_password, role) "
                "VALUES (:iid, :email, :hash, :role)"
            ),
            {"iid": str(institution_id), "email": email, "hash": hashed, "role": role},
        )
    await admin_session.commit()
    return s


@pytest_asyncio.fixture
async def other_seed(admin_session: AsyncSession) -> Seed:
    """Druga institucija — za provjeru izolacije kroz API."""
    suffix = uuid.uuid4().hex[:8]
    institution_id = (
        await admin_session.execute(
            text("INSERT INTO institutions (name_me, name_en) VALUES (:n, :n) RETURNING id"),
            {"n": f"Opština {suffix}"},
        )
    ).scalar_one()
    s = Seed(institution_id, suffix)
    await admin_session.execute(
        text(
            "INSERT INTO users (institution_id, email, hashed_password, role) "
            "VALUES (:iid, :email, :hash, 'caf_lead')"
        ),
        {"iid": str(institution_id), "email": s.caf_lead, "hash": hash_password(PASSWORD)},
    )
    await admin_session.commit()
    return s


async def login(client: AsyncClient, email: str, lang: str = "me") -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD, "lang": lang}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def fill_all_28(client: AsyncClient, headers: dict[str, str], sar_id: str) -> None:
    codes = (await client.get(f"/api/v1/self-assessments/{sar_id}", headers=headers)).json()[
        "subcriteria_scores"
    ]
    assert len(codes) == 28
    body = {
        "score": 3,
        "evidence_text": "Dokaz " * 15,
        "weaknesses_text": "Slabost " * 15,
    }
    for entry in codes:
        r = await client.patch(
            f"/api/v1/self-assessments/{sar_id}/subcriteria/{entry['subcriteria_code']}",
            json=body,
            headers=headers,
        )
        assert r.status_code == 200, r.text


# ---------------------------------------------------------------------- #
# Auth
# ---------------------------------------------------------------------- #
async def test_login_returns_token_with_lang_claim(client: AsyncClient, seed: Seed) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": seed.sponsor, "password": PASSWORD, "lang": "en"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "sponsor"
    assert body["user"]["lang"] == "en"
    assert body["user"]["institution_id"] == str(seed.institution_id)


@pytest.mark.parametrize("lang", ["me", "en"])
async def test_login_wrong_password_is_401_localized(
    client: AsyncClient, seed: Seed, lang: str
) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": seed.sponsor, "password": "pogresna", "lang": lang}
    )
    assert response.status_code == 401
    assert response.json() == {
        "error": "invalid_credentials",
        "message": translate("invalid_credentials", lang),  # type: ignore[arg-type]
    }


async def test_login_unknown_email_same_response_as_wrong_password(
    client: AsyncClient, seed: Seed
) -> None:
    """Ne otkrivamo da li email postoji."""
    unknown = await client.post(
        "/api/v1/auth/login", json={"email": "niko@test.me", "password": PASSWORD, "lang": "me"}
    )
    wrong = await client.post(
        "/api/v1/auth/login", json={"email": seed.sponsor, "password": "x", "lang": "me"}
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


async def test_login_email_is_case_insensitive(client: AsyncClient, seed: Seed) -> None:
    await login(client, seed.sponsor.upper())


async def test_protected_route_without_token_is_401(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/institutions/me")).status_code in (401, 403)


# ---------------------------------------------------------------------- #
# Institutions
# ---------------------------------------------------------------------- #
async def test_institutions_me(client: AsyncClient, seed: Seed) -> None:
    headers = await login(client, seed.employee)
    response = await client.get("/api/v1/institutions/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(seed.institution_id)
    assert body["sag_members_count"] == 3
    assert body["maturity_status"] is None


# ---------------------------------------------------------------------- #
# SAR — kreiranje, uloge, izmjena
# ---------------------------------------------------------------------- #
async def test_employee_cannot_create_sar(client: AsyncClient, seed: Seed) -> None:
    headers = await login(client, seed.employee, lang="en")
    response = await client.post("/api/v1/self-assessments", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"] == "insufficient_role"
    assert response.json()["message"] == translate("insufficient_role", "en")


async def test_caf_lead_creates_sar_and_sees_28_subcriteria(
    client: AsyncClient, seed: Seed
) -> None:
    headers = await login(client, seed.caf_lead)
    created = await client.post("/api/v1/self-assessments", headers=headers)
    assert created.status_code == 201
    sar_id = created.json()["id"]
    assert created.json()["status"] == "draft"

    listing = await client.get("/api/v1/self-assessments", headers=headers)
    assert listing.json()["total"] == 1

    detail = await client.get(f"/api/v1/self-assessments/{sar_id}", headers=headers)
    assert detail.status_code == 200
    scores = detail.json()["subcriteria_scores"]
    assert len(scores) == 28
    assert scores[0]["subcriteria_code"] == "1.1" and scores[0]["score"] is None

    me = await client.get("/api/v1/institutions/me", headers=headers)
    assert me.json()["maturity_status"] == "in_progress"


async def test_patch_subcriteria_sets_quality_flag_and_input_lang(
    client: AsyncClient, seed: Seed
) -> None:
    headers = await login(client, seed.caf_lead, lang="en")
    sar_id = (await client.post("/api/v1/self-assessments", headers=headers)).json()["id"]

    short = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.1",
        json={"evidence_text": "Kratko.", "score": 2},
        headers=headers,
    )
    assert short.status_code == 200, short.text
    assert short.json()["quality_flag"] == "too_short"
    assert short.json()["input_lang"] == "en"  # jezik sesije, CLAUDE.md 6.1

    ok = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.1",
        json={"evidence_text": "riječ " * 25},
        headers=headers,
    )
    assert ok.json()["quality_flag"] == "ok"
    assert ok.json()["score"] == 2  # PATCH ne briše polja koja nisu poslata


async def test_patch_unknown_subcriteria_is_422(client: AsyncClient, seed: Seed) -> None:
    headers = await login(client, seed.caf_lead)
    sar_id = (await client.post("/api/v1/self-assessments", headers=headers)).json()["id"]
    response = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/9.9",
        json={"score": 1},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["error"] == "unknown_subcriteria"


async def test_patch_score_out_of_range_is_422(client: AsyncClient, seed: Seed) -> None:
    headers = await login(client, seed.caf_lead)
    sar_id = (await client.post("/api/v1/self-assessments", headers=headers)).json()["id"]
    response = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.1", json={"score": 6}, headers=headers
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------- #
# SAR — izolacija kroz API
# ---------------------------------------------------------------------- #
async def test_other_institution_cannot_see_or_edit_sar(
    client: AsyncClient, seed: Seed, other_seed: Seed
) -> None:
    mine = await login(client, seed.caf_lead)
    sar_id = (await client.post("/api/v1/self-assessments", headers=mine)).json()["id"]

    theirs = await login(client, other_seed.caf_lead, lang="en")
    assert (await client.get("/api/v1/self-assessments", headers=theirs)).json()["total"] == 0

    get = await client.get(f"/api/v1/self-assessments/{sar_id}", headers=theirs)
    assert get.status_code == 404
    assert get.json() == {"error": "not_found", "message": translate("not_found", "en")}

    patch = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.1", json={"score": 5}, headers=theirs
    )
    assert patch.status_code == 404


# ---------------------------------------------------------------------- #
# Approved Lock kroz API
# ---------------------------------------------------------------------- #
async def test_approve_requires_all_28_scores(client: AsyncClient, seed: Seed) -> None:
    lead = await login(client, seed.caf_lead)
    sar_id = (await client.post("/api/v1/self-assessments", headers=lead)).json()["id"]

    sponsor = await login(client, seed.sponsor, lang="me")
    response = await client.post(f"/api/v1/self-assessments/{sar_id}/approve", headers=sponsor)
    assert response.status_code == 403
    assert response.json() == {
        "error": "sar_incomplete",
        "message": translate("sar_incomplete", "me"),
    }


async def test_only_sponsor_can_approve(client: AsyncClient, seed: Seed) -> None:
    lead = await login(client, seed.caf_lead)
    sar_id = (await client.post("/api/v1/self-assessments", headers=lead)).json()["id"]
    await fill_all_28(client, lead, sar_id)

    response = await client.post(f"/api/v1/self-assessments/{sar_id}/approve", headers=lead)
    assert response.status_code == 403
    assert response.json()["error"] == "insufficient_role"


async def test_full_flow_approve_then_locked_in_both_languages(
    client: AsyncClient, seed: Seed
) -> None:
    lead = await login(client, seed.caf_lead)
    sar_id = (await client.post("/api/v1/self-assessments", headers=lead)).json()["id"]
    await fill_all_28(client, lead, sar_id)

    sponsor_me = await login(client, seed.sponsor, lang="me")
    approved = await client.post(f"/api/v1/self-assessments/{sar_id}/approve", headers=sponsor_me)
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert approved.json()["approved_at"] is not None

    # Idempotentnost NIJE no-op: drugi approve je 409 (kontrakt 4.6).
    again = await client.post(f"/api/v1/self-assessments/{sar_id}/approve", headers=sponsor_me)
    assert again.status_code == 409
    assert again.json() == {"error": "sar_locked", "message": translate("sar_locked", "me")}

    # Izmjena poslije lock-a: 409, poruka na jeziku SESIJE (me pa en).
    locked_me = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.1", json={"score": 5}, headers=lead
    )
    assert locked_me.status_code == 409
    assert locked_me.json()["message"] == translate("sar_locked", "me")

    lead_en = await login(client, seed.caf_lead, lang="en")
    locked_en = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.1", json={"score": 5}, headers=lead_en
    )
    assert locked_en.status_code == 409
    assert locked_en.json()["message"] == translate("sar_locked", "en")

    # Podaci su netaknuti.
    detail = (await client.get(f"/api/v1/self-assessments/{sar_id}", headers=lead_en)).json()
    assert detail["status"] == "approved"
    assert all(s["score"] == 3 for s in detail["subcriteria_scores"])


async def test_db_trigger_is_second_line_of_defence(
    client: AsyncClient, seed: Seed, admin_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Simulira BUG u servisu: provjera statusa (sloj 1) je isključena, SAR
    je odobren direktno u bazi. Trigger 'sar_locked' (sloj 2) mora
    zaustaviti upis, a servis ga mora mapirati na čist 409 — ne na 500.
    """
    from caf.services import sar_service

    lead = await login(client, seed.caf_lead)
    sar_id = (await client.post("/api/v1/self-assessments", headers=lead)).json()["id"]
    await admin_session.execute(
        text("UPDATE self_assessments SET status = 'approved', approved_at = now() WHERE id = :id"),
        {"id": sar_id},
    )
    await admin_session.commit()

    monkeypatch.setattr(sar_service.SarService, "_raise_if_locked", lambda self, sar: None)

    response = await client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.2", json={"score": 2}, headers=lead
    )
    assert response.status_code == 409
    assert response.json()["error"] == "sar_locked"
