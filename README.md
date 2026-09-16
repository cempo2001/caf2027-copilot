# CAF 2027 Copilot

Digitalna platforma za CAF samoprocjenu javne uprave, usklađena sa evropskim CAF 2020/2026 okvirom i CAF Excellence Recognition (CER 2025).

**Prije bilo kakvog rada, pročitaj `CLAUDE.md`** — obavezujuća vodilja za obim, faze, rok (najkasnije februar 2027) i inženjerska pravila. `docs/ARCHITECTURE.md` opisuje strukturu i slojeve, `docs/api-contract-v1.md` API kontrakt, `docs/adr/` arhitektonske odluke.

## Lokalni development

Preduslovi: Docker Desktop, Python 3.12+, Node.js 20+.

```bash
cp .env.example .env
# Popuni .env. OBAVEZNO: DATABASE_URL (app_user, runtime) I ADMIN_DATABASE_URL
# (caf_admin, samo za migracije) — dvije različite role, po dizajnu (ADR-0001).

docker compose up -d postgres redis minio clamav
# clamav: prvi start preuzima potpise (nekoliko minuta) i traži ~3–4 GB RAM-a
# u Docker Desktop-u. Bez njega upload dokaza vraća 503 (fail-closed) — za
# lokalni rad bez ClamAV-a postavi AV_SCAN_MODE=disabled u .env (fajl se
# tada čuva kao "pending", nije verifikovan dokaz; u produkciji zabranjeno).

cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -e ".[dev]"
alembic upgrade head                                # kao caf_admin (ADMIN_DATABASE_URL)
pytest -v                                           # podiže sopstveni Postgres (testcontainers)
uvicorn caf.main:app --reload --port 8765          # http://localhost:8765/api/docs
# (port 8000 je na Windows-u često rezervisan — WinError 10013)
```

## Status

- **Faza:** 1 — backend rute Faze 1 napisane: CIP (5), dokazi sa MinIO + ClamAV (6.1), AI/Consensus predlog sa Offline Math Fallback-om (4.5); migracija `0004`, testovi `tests/test_api_phase1.py` i `tests/test_phase1_units.py`
- **Rok deploy-a:** najkasnije februar 2027 (obim: Faza 0 + Faza 1 — CLAUDE.md 4.0)
- **Otvoreno:** izbor AI provajdera/modela (CLAUDE.md Sekcija 2 — do tada radi samo fallback); provjera naziva podkriterijuma (migracija 0003) naspram zvaničnog EIPA teksta; odvojen MinIO servisni nalog umjesto root naloga (Faza 5)
