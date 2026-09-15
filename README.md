# CAF 2027 Copilot

Digitalna platforma za CAF samoprocjenu javne uprave, usklađena sa evropskim CAF 2020/2026 okvirom i CAF Excellence Recognition (CER 2025).

**Prije bilo kakvog rada, pročitaj `CLAUDE.md`** — obavezujuća vodilja za obim, faze, rok (najkasnije februar 2027) i inženjerska pravila. `docs/ARCHITECTURE.md` opisuje strukturu i slojeve, `docs/api-contract-v1.md` API kontrakt, `docs/adr/` arhitektonske odluke.

## Lokalni development

Preduslovi: Docker Desktop, Python 3.12+, Node.js 20+.

```bash
cp .env.example .env
# Popuni .env. OBAVEZNO: DATABASE_URL (app_user, runtime) I ADMIN_DATABASE_URL
# (caf_admin, samo za migracije) — dvije različite role, po dizajnu (ADR-0001).

docker compose up -d postgres redis minio

cd backend
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -e ".[dev]"
alembic upgrade head                                # kao caf_admin (ADMIN_DATABASE_URL)
pytest -v                                           # podiže sopstveni Postgres (testcontainers)
uvicorn caf.main:app --reload --port 8765          # http://localhost:8765/api/docs
# (port 8000 je na Windows-u često rezervisan — WinError 10013)
```

## Status

- **Faza:** 0 → zatvara se (baza, RLS, Approved Lock, auth, SAR API — sve testirano)
- **Rok deploy-a:** najkasnije februar 2027 (obim: Faza 0 + Faza 1 — CLAUDE.md 4.0)
- **Otvoreno prije Faze 1 UI-ja:** zvanični tekst 28 podkriterijuma (EIPA) u `subcriteria` tabelu
