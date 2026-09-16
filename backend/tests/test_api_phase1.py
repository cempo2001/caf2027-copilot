"""
API tokovi Faze 1 kroz HTTP, protiv testcontainers baze (migracije do
0004), kao `app_user` — isti put kao produkcija:

- CIP akcioni plan (api-contract-v1.md 5)
- upload dokaza (6.1) — trezor i antivirus su lažni (in-memory), ali
  cijeli servisni tok, RLS, Approved Lock i upis metapodataka su pravi
- AI/Consensus predlog sa Offline Math Fallback-om (4.5)

Greške se provjeravaju na OBA jezika gdje je to smisleno (CLAUDE.md 6.3).
"""

import hashlib
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from caf.api.deps import get_ai_provider, get_av_scanner, get_object_storage
from caf.core.config import Settings, get_settings
from caf.core.i18n import translate
from caf.db.session import create_session_factory, get_db_session
from caf.integrations.ai_provider import AiProviderError, AiSuggestion
from caf.integrations.clamav import AvScannerError, ScanResult, ScanVerdict
from caf.integrations.object_storage import ObjectStorageError
from caf.main import create_app
from caf.services.sar_access import SarAccess

# Fixture-i i pomoćne funkcije iz toka Faze 0 (isti seed, isti login).
from tests.test_api_sar_flow import (  # noqa: F401
    Seed,
    api_settings,
    fill_all_28,
    login,
    other_seed,
    seed,
)

PDF_BYTES = b"%PDF-1.7\n" + b"sadrzaj dokaza " * 50
EVIDENCE_ME = (
    "Institucija je donijela strateški plan sa jasno definisanim ciljevima. Plan je sproveden "
    "kroz obuke zaposlenih i realizovane projekte. Rezultati se prate kroz kvartalne izvještaje "
    "i ankete, a na osnovu analiza procesi su unaprijeđeni i ažurirani."
)


# ---------------------------------------------------------------------- #
# Lažni spoljni servisi
# ---------------------------------------------------------------------- #
@dataclass
class FakeStorage:
    objects: dict[str, tuple[bytes, str, dict[str, str]]] = field(default_factory=dict)
    fail_put: bool = False
    deleted: list[str] = field(default_factory=list)

    async def put(
        self, key: str, data: bytes, *, content_type: str, metadata: dict[str, str]
    ) -> None:
        if self.fail_put:
            raise ObjectStorageError("simulirano: trezor nedostupan")
        self.objects[key] = (data, content_type, metadata)

    async def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.objects.pop(key, None)


@dataclass
class FakeScanner:
    result: ScanResult = field(default_factory=lambda: ScanResult(ScanVerdict.CLEAN))
    unavailable: bool = False
    scanned: int = 0

    async def scan(self, data: bytes) -> ScanResult:
        self.scanned += 1
        if self.unavailable:
            raise AvScannerError("simulirano: clamd ne odgovara")
        return self.result


@dataclass
class FakeProvider:
    suggestion: AiSuggestion | None = None
    error: bool = False

    async def suggest(self, **_: Any) -> AiSuggestion:
        if self.error or self.suggestion is None:
            raise AiProviderError("simulirano: provajder pao")
        return self.suggestion


@dataclass
class Api:
    client: AsyncClient
    storage: FakeStorage
    scanner: FakeScanner
    overrides: dict[Any, Any]

    def disable_scanner(self) -> None:
        self.overrides[get_av_scanner] = lambda: None

    def use_provider(self, provider: FakeProvider) -> None:
        self.overrides[get_ai_provider] = lambda: provider


@pytest_asyncio.fixture
async def api(app_user_engine: AsyncEngine, api_settings: Settings) -> AsyncGenerator[Api, None]:
    app = create_app()
    factory = create_session_factory(app_user_engine)

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    storage, scanner = FakeStorage(), FakeScanner()
    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_settings] = lambda: api_settings
    app.dependency_overrides[get_object_storage] = lambda: storage
    app.dependency_overrides[get_av_scanner] = lambda: scanner
    app.dependency_overrides[get_ai_provider] = lambda: None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield Api(http, storage, scanner, app.dependency_overrides)


async def new_sar(api: Api, headers: dict[str, str]) -> str:
    created = await api.client.post("/api/v1/self-assessments", headers=headers)
    assert created.status_code == 201, created.text
    return str(created.json()["id"])


async def approved_sar(api: Api, seed: Seed) -> tuple[str, dict[str, str]]:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await fill_all_28(api.client, lead, sar_id)
    sponsor = await login(api.client, seed.sponsor)
    approved = await api.client.post(f"/api/v1/self-assessments/{sar_id}/approve", headers=sponsor)
    assert approved.status_code == 200, approved.text
    return sar_id, lead


async def approve_directly_in_db(admin_session: AsyncSession, sar_id: str) -> None:
    await admin_session.execute(
        text("UPDATE self_assessments SET status = 'approved', approved_at = now() WHERE id = :id"),
        {"id": sar_id},
    )
    await admin_session.commit()


def skip_service_lock_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulira bug u servisu: sloj 1 isključen, ostaje samo trigger (sloj 2)."""
    monkeypatch.setattr(SarAccess, "load_unlocked_sar", SarAccess.load_sar)


CIP_BODY = {
    "title_me": "Uvesti kvartalno praćenje strategije",
    "title_en": "Introduce quarterly strategy monitoring",
    "quadrant": "quick_win",
    "as_is": "Strategija se ne prati sistematski.",
    "to_be": "Kvartalni izvještaj o sprovođenju strategije.",
}


# ====================================================================== #
# 5. CIP
# ====================================================================== #
async def test_cip_create_and_list(api: Api, seed: Seed) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)

    empty = await api.client.get(f"/api/v1/self-assessments/{sar_id}/cip", headers=lead)
    assert empty.status_code == 200
    assert empty.json() == {"items": []}

    created = await api.client.post(
        f"/api/v1/self-assessments/{sar_id}/cip", json=CIP_BODY, headers=lead
    )
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["status"] == "planned"
    assert {k: item[k] for k in CIP_BODY} == CIP_BODY

    employee = await login(api.client, seed.employee)
    listing = await api.client.get(f"/api/v1/self-assessments/{sar_id}/cip", headers=employee)
    assert listing.status_code == 200
    assert [i["id"] for i in listing.json()["items"]] == [item["id"]]


async def test_cip_employee_cannot_create(api: Api, seed: Seed) -> None:
    sar_id = await new_sar(api, await login(api.client, seed.caf_lead))
    employee = await login(api.client, seed.employee, lang="en")
    response = await api.client.post(
        f"/api/v1/self-assessments/{sar_id}/cip", json=CIP_BODY, headers=employee
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": "insufficient_role",
        "message": translate("insufficient_role", "en"),
    }


@pytest.mark.parametrize(
    "patch",
    [
        {"title_me": "   "},
        {"as_is": ""},
        {"quadrant": "urgent"},
        {"title_en": "x" * 301},
    ],
)
async def test_cip_validation_is_422(api: Api, seed: Seed, patch: dict[str, str]) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    response = await api.client.post(
        f"/api/v1/self-assessments/{sar_id}/cip", json={**CIP_BODY, **patch}, headers=lead
    )
    assert response.status_code == 422


async def test_cip_other_institution_gets_404(api: Api, seed: Seed, other_seed: Seed) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await api.client.post(f"/api/v1/self-assessments/{sar_id}/cip", json=CIP_BODY, headers=lead)

    theirs = await login(api.client, other_seed.caf_lead)
    get = await api.client.get(f"/api/v1/self-assessments/{sar_id}/cip", headers=theirs)
    post = await api.client.post(
        f"/api/v1/self-assessments/{sar_id}/cip", json=CIP_BODY, headers=theirs
    )
    assert get.status_code == post.status_code == 404


async def test_cip_locked_after_approval_both_languages(api: Api, seed: Seed) -> None:
    sar_id, lead = await approved_sar(api, seed)

    for lang in ("me", "en"):
        headers = await login(api.client, seed.caf_lead, lang=lang)
        response = await api.client.post(
            f"/api/v1/self-assessments/{sar_id}/cip", json=CIP_BODY, headers=headers
        )
        assert response.status_code == 409
        assert response.json() == {
            "error": "sar_locked",
            "message": translate("sar_locked", lang),  # type: ignore[arg-type]
        }

    # Čitanje zaključanog plana je i dalje dozvoljeno.
    listing = await api.client.get(f"/api/v1/self-assessments/{sar_id}/cip", headers=lead)
    assert listing.status_code == 200


async def test_cip_db_trigger_is_second_line_of_defence(
    api: Api, seed: Seed, admin_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await approve_directly_in_db(admin_session, sar_id)
    skip_service_lock_check(monkeypatch)

    response = await api.client.post(
        f"/api/v1/self-assessments/{sar_id}/cip", json=CIP_BODY, headers=lead
    )
    assert response.status_code == 409
    assert response.json()["error"] == "sar_locked"


# ====================================================================== #
# 6.1 Evidence
# ====================================================================== #
def _upload(api: Api, sar_id: str, headers: dict[str, str], *, name: str = "izvjestaj.pdf",
            content: bytes = PDF_BYTES, code: str = "1.1") -> Any:
    return api.client.post(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/{code}/evidence",
        files={"file": (name, content, "application/octet-stream")},
        headers=headers,
    )


async def test_evidence_clean_upload_is_stored(
    api: Api, seed: Seed, admin_session: AsyncSession
) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)

    response = await _upload(api, sar_id, lead, name="..\\..\\Izvještaj 2026.pdf")
    assert response.status_code == 201, response.text
    body = response.json()
    digest = hashlib.sha256(PDF_BYTES).hexdigest()
    assert body["sha256"] == digest
    assert body["av_scan_status"] == "clean"
    assert body["filename"] == "Izvještaj 2026.pdf"  # putanja odsječena

    assert api.scanner.scanned == 1
    [(key, (data, content_type, metadata))] = api.storage.objects.items()
    assert key.startswith(f"{seed.institution_id}/{sar_id}/1.1/")
    assert "Izvj" not in key  # korisničko ime fajla nije u ključu
    assert data == PDF_BYTES
    assert content_type == "application/pdf"  # naš tip, ne klijentov
    assert metadata["sha256"] == digest

    row = (
        await admin_session.execute(
            text(
                "SELECT institution_id, object_key, av_scan_status, size_bytes "
                "FROM evidence_files WHERE id = :id"
            ),
            {"id": body["id"]},
        )
    ).one()
    assert str(row.institution_id) == str(seed.institution_id)
    assert row.object_key == key
    assert row.av_scan_status == "clean"
    assert row.size_bytes == len(PDF_BYTES)


@pytest.mark.parametrize("lang", ["me", "en"])
async def test_evidence_infected_is_rejected_and_not_stored(
    api: Api, seed: Seed, admin_session: AsyncSession, lang: str
) -> None:
    api.scanner.result = ScanResult(ScanVerdict.INFECTED, "Win.Test.EICAR_HDB-1")
    lead = await login(api.client, seed.caf_lead, lang=lang)
    sar_id = await new_sar(api, lead)

    response = await _upload(api, sar_id, lead)
    assert response.status_code == 422
    assert response.json() == {
        "error": "evidence_infected",
        "message": translate("evidence_infected", lang),  # type: ignore[arg-type]
    }
    assert api.storage.objects == {}
    count = await admin_session.scalar(
        text("SELECT count(*) FROM evidence_files WHERE self_assessment_id = :id"), {"id": sar_id}
    )
    assert count == 0


async def test_evidence_scanner_down_fails_closed(api: Api, seed: Seed) -> None:
    api.scanner.unavailable = True
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)

    response = await _upload(api, sar_id, lead)
    assert response.status_code == 503
    assert response.json()["error"] == "av_scanner_unavailable"
    assert api.storage.objects == {}


async def test_evidence_scan_disabled_marks_pending(api: Api, seed: Seed) -> None:
    api.disable_scanner()
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)

    response = await _upload(api, sar_id, lead)
    assert response.status_code == 201, response.text
    assert response.json()["av_scan_status"] == "pending"
    assert api.scanner.scanned == 0


async def test_evidence_storage_down_is_503_and_nothing_recorded(
    api: Api, seed: Seed, admin_session: AsyncSession
) -> None:
    api.storage.fail_put = True
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)

    response = await _upload(api, sar_id, lead)
    assert response.status_code == 503
    assert response.json()["error"] == "storage_unavailable"
    count = await admin_session.scalar(
        text("SELECT count(*) FROM evidence_files WHERE self_assessment_id = :id"), {"id": sar_id}
    )
    assert count == 0


@pytest.mark.parametrize(
    ("name", "content", "error"),
    [
        ("program.exe", b"MZ\x90\x00", "evidence_type_not_allowed"),
        ("prerusen.pdf", b"MZ\x90\x00" * 10, "evidence_type_not_allowed"),
        ("prazan.pdf", b"", "validation_error"),
    ],
)
async def test_evidence_bad_files_are_422(
    api: Api, seed: Seed, name: str, content: bytes, error: str
) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    response = await _upload(api, sar_id, lead, name=name, content=content)
    assert response.status_code == 422
    assert response.json()["error"] == error
    assert api.storage.objects == {}
    assert api.scanner.scanned == 0  # odbijeno prije skeniranja


async def test_evidence_too_large_is_422(
    api: Api, seed: Seed, api_settings: Settings
) -> None:
    api.overrides[get_settings] = lambda: api_settings.model_copy(
        update={"max_evidence_bytes": 1024}
    )
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    response = await _upload(api, sar_id, lead, content=b"%PDF-" + b"x" * 2048)
    assert response.status_code == 422
    assert response.json()["error"] == "evidence_too_large"


async def test_evidence_access_rules(api: Api, seed: Seed, other_seed: Seed) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)

    employee = await login(api.client, seed.employee)
    assert (await _upload(api, sar_id, employee)).status_code == 403

    unknown = await _upload(api, sar_id, lead, code="9.9")
    assert unknown.status_code == 422
    assert unknown.json()["error"] == "unknown_subcriteria"

    theirs = await login(api.client, other_seed.caf_lead)
    assert (await _upload(api, sar_id, theirs)).status_code == 404

    missing_field = await api.client.post(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/1.1/evidence", headers=lead
    )
    assert missing_field.status_code == 422
    assert api.storage.objects == {}


async def test_evidence_locked_after_approval(api: Api, seed: Seed) -> None:
    sar_id, lead = await approved_sar(api, seed)
    response = await _upload(api, sar_id, lead)
    assert response.status_code == 409
    assert response.json()["error"] == "sar_locked"
    assert api.storage.objects == {}


async def test_evidence_object_removed_when_db_write_is_blocked(
    api: Api, seed: Seed, admin_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Trigger odbije upis POSLIJE uploada u trezor -> objekat se briše (nema siročića)."""
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await approve_directly_in_db(admin_session, sar_id)
    skip_service_lock_check(monkeypatch)

    response = await _upload(api, sar_id, lead)
    assert response.status_code == 409
    assert response.json()["error"] == "sar_locked"
    assert len(api.storage.deleted) == 1
    assert api.storage.objects == {}


# ====================================================================== #
# 4.5 AI/Consensus
# ====================================================================== #
def _consensus_url(sar_id: str, code: str = "1.1") -> str:
    return f"/api/v1/self-assessments/{sar_id}/subcriteria/{code}/ai-consensus"


async def _save_evidence(
    api: Api, sar_id: str, headers: dict[str, str], code: str = "1.1", text_: str = EVIDENCE_ME
) -> None:
    saved = await api.client.patch(
        f"/api/v1/self-assessments/{sar_id}/subcriteria/{code}",
        json={"evidence_text": text_, "weaknesses_text": "Nedostaje sistematsko praćenje."},
        headers=headers,
    )
    assert saved.status_code == 200, saved.text


@pytest.mark.parametrize("lang", ["me", "en"])
async def test_consensus_requires_saved_evidence(api: Api, seed: Seed, lang: str) -> None:
    lead = await login(api.client, seed.caf_lead, lang=lang)
    sar_id = await new_sar(api, lead)
    response = await api.client.post(_consensus_url(sar_id), headers=lead)
    assert response.status_code == 422
    assert response.json() == {
        "error": "consensus_needs_evidence",
        "message": translate("consensus_needs_evidence", lang),  # type: ignore[arg-type]
    }


async def test_consensus_fallback_without_provider(api: Api, seed: Seed) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await _save_evidence(api, sar_id, lead)
    before = (await api.client.get(f"/api/v1/self-assessments/{sar_id}", headers=lead)).json()

    response = await api.client.post(_consensus_url(sar_id), headers=lead)
    assert response.status_code == 200, response.text
    assert response.headers["X-Consensus-Warning"] == "ai_provider_unavailable"
    body = response.json()
    assert body["source"] == "fallback"
    assert body["requires_human_confirmation"] is True
    assert set(body["breakdown"]) == {"plan", "do", "check", "act"}
    assert 1 <= body["suggested_score"] <= 5
    assert body["suggested_summary_text"].startswith("Offline procjena")

    # Human-in-the-loop: ništa nije upisano.
    after = (await api.client.get(f"/api/v1/self-assessments/{sar_id}", headers=lead)).json()
    assert after == before


async def test_consensus_labels_follow_session_language(api: Api, seed: Seed) -> None:
    lead_me = await login(api.client, seed.caf_lead, lang="me")
    sar_id = await new_sar(api, lead_me)
    await _save_evidence(api, sar_id, lead_me, code="6.1")

    lead_en = await login(api.client, seed.caf_lead, lang="en")
    body = (await api.client.post(_consensus_url(sar_id, "6.1"), headers=lead_en)).json()
    assert set(body["breakdown"]) == {"measurement", "trend", "target", "comparison"}
    assert body["suggested_summary_text"].startswith("Offline assessment")
    assert "Institucija je donijela" in body["suggested_summary_text"]  # bez prevođenja


async def test_consensus_uses_ai_provider_when_available(api: Api, seed: Seed) -> None:
    api.use_provider(FakeProvider(suggestion=AiSuggestion(score=4, summary="AI obrazloženje")))
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await _save_evidence(api, sar_id, lead)

    response = await api.client.post(_consensus_url(sar_id), headers=lead)
    assert response.status_code == 200
    assert "X-Consensus-Warning" not in response.headers
    assert response.json()["source"] == "ai"
    assert response.json()["suggested_score"] == 4


@pytest.mark.parametrize(
    "provider",
    [FakeProvider(error=True), FakeProvider(suggestion=AiSuggestion(score=9, summary="x"))],
)
async def test_consensus_falls_back_when_provider_fails_or_is_invalid(
    api: Api, seed: Seed, provider: FakeProvider
) -> None:
    api.use_provider(provider)
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await _save_evidence(api, sar_id, lead)

    response = await api.client.post(_consensus_url(sar_id), headers=lead)
    assert response.status_code == 200
    assert response.json()["source"] == "fallback"
    assert response.headers["X-Consensus-Warning"] == "ai_provider_unavailable"


async def test_consensus_access_rules(api: Api, seed: Seed, other_seed: Seed) -> None:
    lead = await login(api.client, seed.caf_lead)
    sar_id = await new_sar(api, lead)
    await _save_evidence(api, sar_id, lead)

    employee = await login(api.client, seed.employee)
    assert (await api.client.post(_consensus_url(sar_id), headers=employee)).status_code == 403

    unknown = await api.client.post(_consensus_url(sar_id, "9.9"), headers=lead)
    assert unknown.status_code == 422
    assert unknown.json()["error"] == "unknown_subcriteria"

    theirs = await login(api.client, other_seed.caf_lead)
    assert (await api.client.post(_consensus_url(sar_id), headers=theirs)).status_code == 404


async def test_consensus_locked_after_approval(api: Api, seed: Seed) -> None:
    sar_id, lead = await approved_sar(api, seed)
    response = await api.client.post(_consensus_url(sar_id), headers=lead)
    assert response.status_code == 409
    assert response.json()["error"] == "sar_locked"
