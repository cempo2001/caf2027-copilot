"""
Jedinični testovi Faze 1 bez baze i bez Docker-a:
- Offline Math Fallback (api-contract-v1.md 4.5, CLAUDE.md 7.5)
- pravila za fajlove dokaza i clamd INSTREAM klijent (6.1, CLAUDE.md 7.6)
- sigurnosna pravila konfiguracije (produkcija ne smije bez AV-a / TLS-a)
"""

import asyncio
import struct

import pytest
from pydantic import ValidationError

from caf.core.config import Settings
from caf.integrations.clamav import (
    AvScannerError,
    ClamdScanner,
    ScanVerdict,
    parse_clamd_reply,
)
from caf.services import consensus_fallback as fb
from caf.services.evidence_files import detect_kind, sanitize_filename

ME_RICH = (
    "Institucija je donijela strateški plan sa jasno definisanim ciljevima. Plan je sproveden "
    "kroz obuke zaposlenih i realizovane projekte. Rezultati se prate kroz kvartalne izvještaje "
    "i ankete, a na osnovu analiza procesi su unaprijeđeni i ažurirani."
)
ME_POOR = (
    "Imamo neke dokumente o radu institucije koje koristimo u svakodnevnom radu i nekada ih "
    "pogledamo kada treba nešto uraditi u instituciji."
)
EN_RICH = (
    "We defined strategic objectives and priorities, implemented staff training and delivered "
    "the programme, monitor KPIs through quarterly reports and surveys, and improved and "
    "updated our processes based on lessons learned during the annual review."
)


# ---------------------------------------------------------------------- #
# Offline Math Fallback
# ---------------------------------------------------------------------- #
def test_fallback_rich_montenegrin_evidence_scores_high() -> None:
    result = fb.suggest(
        criterion_number=1, evidence=ME_RICH, weaknesses=None, input_lang="me", session_lang="me"
    )
    assert set(result.breakdown) == set(fb.ENABLER_DIMENSIONS)
    assert all(v >= 3 for v in result.breakdown.values())
    assert result.score == 4
    assert result.summary.startswith("Offline procjena")


def test_fallback_poor_evidence_scores_one() -> None:
    result = fb.suggest(
        criterion_number=2, evidence=ME_POOR, weaknesses=None, input_lang="me", session_lang="me"
    )
    assert result.score == 1
    assert result.breakdown == {"plan": 1, "do": 1, "check": 1, "act": 1}


def test_fallback_is_deterministic() -> None:
    kwargs = dict(
        criterion_number=3, evidence=EN_RICH, weaknesses="x", input_lang="en", session_lang="en"
    )
    assert fb.suggest(**kwargs) == fb.suggest(**kwargs)  # type: ignore[arg-type]


def test_fallback_caps_short_evidence() -> None:
    short = "Strateški plan, sprovedene obuke, praćenje izvještaja, unaprijeđeni procesi."
    result = fb.suggest(
        criterion_number=1, evidence=short, weaknesses=None, input_lang="me", session_lang="me"
    )
    assert sum(result.breakdown.values()) / 4 > fb.SHORT_EVIDENCE_CAP
    assert result.score == fb.SHORT_EVIDENCE_CAP
    assert f"< {fb.MIN_EVIDENCE_WORDS}" in result.summary


def test_fallback_uses_results_panel_for_criteria_6_to_9() -> None:
    evidence = (
        "Anketa zadovoljstva korisnika pokazuje porast od 12% u odnosu na prošlu godinu, "
        "iznad ciljne vrijednosti i prosjeka drugih institucija u regionu, "
        "podaci se prikupljaju godišnje."
    )
    result = fb.suggest(
        criterion_number=6, evidence=evidence, weaknesses=None, input_lang="me", session_lang="en"
    )
    assert set(result.breakdown) == set(fb.RESULT_DIMENSIONS)
    assert result.score >= 3
    assert "Measurement" in result.summary  # oznake na jeziku SESIJE


def test_fallback_indicators_follow_input_language_not_session() -> None:
    """CLAUDE.md 6.1: crnogorski tekst se ocjenjuje crnogorskim listama i kad je sesija en."""
    me_list = fb.suggest(
        criterion_number=1, evidence=ME_RICH, weaknesses=None, input_lang="me", session_lang="en"
    )
    en_list = fb.suggest(
        criterion_number=1, evidence=ME_RICH, weaknesses=None, input_lang="en", session_lang="en"
    )
    assert me_list.score > en_list.score
    assert "Plan " in me_list.summary and "Planiranje" not in me_list.summary


def test_fallback_quotes_user_text_without_translation() -> None:
    result = fb.suggest(
        criterion_number=1,
        evidence=ME_RICH,
        weaknesses="Nedostaje sistematsko praćenje. Druga rečenica.",
        input_lang="me",
        session_lang="en",
    )
    assert "Institucija je donijela strateški plan" in result.summary
    assert "Stated weaknesses: Nedostaje sistematsko praćenje." in result.summary
    assert "Druga rečenica" not in result.summary


def test_normalize_strips_diacritics() -> None:
    assert fb.normalize("Unaprijeđeni ČĆŠŽ") == "unaprijedjeni ccsz"


# ---------------------------------------------------------------------- #
# Fajlovi dokaza
# ---------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\x\\Izvještaj 2026.pdf", "Izvještaj 2026.pdf"),
        ("a\x00b\n.pdf", "ab.pdf"),
        ('bad<>:"|?*.txt', "bad.txt"),
        ("  .  ", "dokaz"),
        (None, "dokaz"),
    ],
)
def test_sanitize_filename(raw: str | None, expected: str) -> None:
    assert sanitize_filename(raw) == expected


def test_sanitize_filename_keeps_extension_when_truncating() -> None:
    name = sanitize_filename("x" * 400 + ".docx")
    assert len(name) == 255 and name.endswith(".docx")


@pytest.mark.parametrize(
    ("filename", "head", "allowed"),
    [
        ("r.pdf", b"%PDF-1.7", True),
        ("r.PDF", b"%PDF-1.7", True),
        ("r.pdf", b"MZ\x90\x00", False),  # preimenovan izvršni fajl
        ("r.exe", b"MZ\x90\x00", False),
        ("a.docx", b"PK\x03\x04rest", True),
        ("a.png", b"\x89PNG\r\n\x1a\n", True),
        ("a.csv", b"a,b\n1,2", True),
        ("a.txt", b"x\x00y", False),  # binarni sadržaj u .txt
        ("pdf", b"%PDF-", False),  # bez ekstenzije
        (".pdf", b"%PDF-", False),
    ],
)
def test_detect_kind(filename: str, head: bytes, allowed: bool) -> None:
    assert (detect_kind(filename, head) is not None) is allowed


# ---------------------------------------------------------------------- #
# clamd INSTREAM klijent (lažni clamd server)
# ---------------------------------------------------------------------- #
async def _fake_clamd(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    assert await reader.readuntil(b"\0") == b"zINSTREAM\0"
    data = bytearray()
    while True:
        (size,) = struct.unpack("!L", await reader.readexactly(4))
        if size == 0:
            break
        data += await reader.readexactly(size)
    if b"EICAR" in data:
        writer.write(b"stream: Win.Test.EICAR_HDB-1 FOUND\0")
    elif data.startswith(b"ERR"):
        writer.write(b"INSTREAM size limit exceeded. ERROR\0")
    else:
        writer.write(b"stream: OK\0")
    await writer.drain()
    writer.close()


async def test_clamd_scanner_clean_infected_and_error() -> None:
    server = await asyncio.start_server(_fake_clamd, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    scanner = ClamdScanner("127.0.0.1", port, timeout_seconds=5)
    try:
        clean = await scanner.scan(b"a" * (200 * 1024 + 7))  # više chunk-ova
        assert clean.verdict is ScanVerdict.CLEAN

        infected = await scanner.scan(b"...EICAR...")
        assert infected.verdict is ScanVerdict.INFECTED
        assert infected.signature == "Win.Test.EICAR_HDB-1"

        with pytest.raises(AvScannerError):
            await scanner.scan(b"ERR")
    finally:
        server.close()
        await server.wait_closed()


async def test_clamd_scanner_unreachable_is_error() -> None:
    server = await asyncio.start_server(_fake_clamd, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    server.close()
    await server.wait_closed()
    with pytest.raises(AvScannerError):
        await ClamdScanner("127.0.0.1", port, timeout_seconds=2).scan(b"x")


async def test_clamd_scanner_timeout_is_error() -> None:
    async def _hang(_: asyncio.StreamReader, __: asyncio.StreamWriter) -> None:
        await asyncio.sleep(2)

    server = await asyncio.start_server(_hang, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        with pytest.raises(AvScannerError):
            await ClamdScanner("127.0.0.1", port, timeout_seconds=0.3).scan(b"x")
    finally:
        server.close()


@pytest.mark.parametrize("raw", [b"garbage", b"stream: weird\0", b""])
def test_parse_clamd_reply_rejects_unknown(raw: bytes) -> None:
    with pytest.raises(AvScannerError):
        parse_clamd_reply(raw)


# ---------------------------------------------------------------------- #
# Konfiguracija — Security by Design
# ---------------------------------------------------------------------- #
def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = dict(
        _env_file=None,
        database_url="postgresql+asyncpg://u:p@localhost:5432/db",
        redis_url="redis://localhost:6379/0",
        minio_endpoint="localhost:9000",
        minio_root_user="u",
        minio_root_password="p",
        jwt_secret_key="k" * 40,
    )
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_production_refuses_disabled_av_scan() -> None:
    with pytest.raises(ValidationError):
        _settings(environment="production", av_scan_mode="disabled", minio_secure=True)


def test_production_refuses_minio_without_tls() -> None:
    with pytest.raises(ValidationError):
        _settings(environment="production", minio_secure=False)


def test_development_allows_disabled_av_scan() -> None:
    assert _settings(av_scan_mode="disabled").av_scan_mode == "disabled"
