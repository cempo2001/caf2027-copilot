# ARCHITECTURE.md — CAF 2027 Copilot: Temelj (Backend + Frontend)

Prati CLAUDE.md (obavezujuća pravila). Ovo je struktura repozitorijuma i slojevi PRE nego što se piše prva linija poslovne logike — "temelj kuće" za Fazu 0 + Fazu 1 (Nivo 1: Institucija).

---

## 1. Monorepo — struktura na najvišem nivou

```
caf2027-copilot/
├── backend/                 # FastAPI aplikacija (Python 3.12+)
├── frontend/                 # Next.js 15 aplikacija (React 19)
├── infra/                    # Docker, docker-compose, CI konfiguracija
├── docs/                     # ADR-ovi, CLAUDE.md, ARCHITECTURE.md, API kontrakti
├── .github/workflows/        # CI pipeline (DevOps agent, Sekcija 8.8)
└── docker-compose.yml        # Lokalni dev: postgres, redis, minio, backend, frontend
```

Monorepo (ne odvojeni repoi) — jer Frontend i Backend agenti moraju raditi na sinhronizovanim API kontraktima (Sekcija 8.9: Arhitekta definiše kontrakt prije nego što oba agenta počnu paralelno).

---

## 2. Backend — FastAPI, slojevita arhitektura (Sekcija 3, pravilo 2)

```
backend/
├── src/
│   └── caf/
│       ├── main.py                      # FastAPI app factory, middleware, router registracija
│       ├── core/
│       │   ├── config.py                # Pydantic BaseSettings — .env, nema hardkodovanih tajni
│       │   ├── security.py              # JWT encode/decode, custom claims (tenant_id, role, lang)
│       │   ├── i18n.py                  # Jezik iz claim-a/Accept-Language → context za servise (Sekcija 6.2)
│       │   └── exceptions.py            # Custom exception klase (LockedSarError, TenantMismatchError...)
│       │
│       ├── db/
│       │   ├── session.py               # Async SQLAlchemy engine + session factory
│       │   ├── base.py                  # Declarative base
│       │   └── rls.py                   # Helper za postavljanje `app.current_institution_id` po sesiji
│       │
│       ├── models/                      # ORM slojevi (SQLAlchemy 2.0) — jedan fajl po agregatu
│       │   ├── institution.py
│       │   ├── user.py
│       │   ├── self_assessment.py
│       │   ├── subcriteria_score.py
│       │   └── evidence.py              # MinIO metapodaci (Vault agent, Sekcija 8.6)
│       │
│       ├── schemas/                     # Pydantic v2 DTO — Request/Response, odvojeno od ORM-a
│       │   ├── institution.py
│       │   ├── user.py
│       │   ├── self_assessment.py
│       │   └── common.py                # Paginacija, error response format (lokalizovan, Sekcija 6.1)
│       │
│       ├── services/                    # Poslovna logika — jedini sloj koji "zna" pravila
│       │   ├── sar_service.py           # SAR CRUD, Approved Lock provjera (409)
│       │   ├── consensus_service.py     # AI + Offline Math Fallback (AI/Consensus agent, 8.5)
│       │   ├── cip_service.py           # CIP akcioni plan, 2x2 matrica
│       │   └── evidence_service.py      # MinIO upload, SHA-256, ClamAV poziv
│       │
│       ├── api/
│       │   ├── deps.py                  # get_current_user, get_db_session, get_language
│       │   └── v1/
│       │       ├── router.py            # Agregira sve v1 routere
│       │       ├── institutions.py      # Router sloj — TANAK, samo poziva servise
│       │       ├── self_assessments.py
│       │       └── auth.py
│       │
│       └── alembic/                     # Migracije (Database agent, 8.2)
│           ├── env.py
│           └── versions/
│
├── tests/
│   ├── conftest.py                      # testcontainers: postgres + redis fixture
│   ├── test_rls_isolation.py            # KRITIČNO — dokazuje tenant izolaciju
│   ├── test_approved_lock.py            # KRITIČNO — dokazuje 409 na zaključan SAR
│   ├── test_consensus_fallback.py       # Offline Math Fallback bez interneta
│   └── test_i18n_error_messages.py      # Greške lokalizovane na oba jezika (Sekcija 6.3)
│
├── pyproject.toml
├── .env.example                         # Nikad .env sa pravim vrijednostima u repo
└── Dockerfile
```

**Pravilo sloja (strogo):** Router → poziva Service → Service koristi Model (ORM) i vraća Schema (DTO). Router **nikad** direktno ne pipa ORM model niti piše SQL. Service **nikad** ne zna za HTTP (nema `Request`/`Response` objekata u servisima) — to omogućava da se servisi testiraju bez podizanja API sloja.

---

## 3. Frontend — Next.js 15 App Router, feature-based struktura

```
frontend/
├── src/
│   ├── app/
│   │   ├── [locale]/                    # next-intl — jezik u ruti: /me/... i /en/... (Sekcija 6.2)
│   │   │   ├── layout.tsx               # Root layout po jeziku, tema (svijetla/tamna)
│   │   │   ├── (auth)/
│   │   │   │   └── login/page.tsx
│   │   │   ├── (institution)/           # Nivo 1 — role-gated route group
│   │   │   │   ├── wizard/[subcriteriaId]/page.tsx    # Vođeni Čarobnjak
│   │   │   │   ├── sar/[sarId]/page.tsx               # Pregled SAR-a
│   │   │   │   ├── cip/page.tsx                       # 2x2 matrica akcionog plana
│   │   │   │   └── dashboard/page.tsx                 # Sponsor/Ministar radar spidogram
│   │   │   └── globals.css
│   │   └── api/                         # Next.js Route Handlers SAMO za BFF potrebe (ne poslovna logika)
│   │
│   ├── features/                        # Feature-first — ne "components/ i pages/" generički
│   │   ├── wizard/
│   │   │   ├── components/              # WizardStep.tsx, QualityIndicator.tsx...
│   │   │   ├── hooks/                   # useWizardProgress.ts
│   │   │   └── actions.ts               # Server Actions — pozivaju backend API, tipizovano
│   │   ├── sar/
│   │   ├── cip/
│   │   └── auth/
│   │
│   ├── components/ui/                   # Shadcn UI primitive (dugme, input, dialog...) — bez poslovne logike
│   │
│   ├── i18n/
│   │   ├── messages/
│   │   │   ├── me.json                  # Crnogorski prevodi
│   │   │   └── en.json                  # Engleski prevodi
│   │   └── request.ts                   # next-intl config
│   │
│   ├── lib/
│   │   ├── api-client.ts                # Tipizovan fetch wrapper ka FastAPI (šalje Accept-Language, JWT)
│   │   └── auth.ts                      # Session/JWT handling na frontendu
│   │
│   └── types/
│       └── api.ts                       # Generisano ili ručno sinhronizovano sa backend Pydantic schemas
│
├── public/
├── next.config.ts
├── package.json
└── Dockerfile
```

**Pravilo sloja:** `app/` sadrži samo rutiranje i layout — nikad poslovnu logiku. `features/*/actions.ts` je jedino mjesto koje zove backend. Komponente u `components/ui/` ne smiju znati ništa o SAR-u, CIP-u ili CAF terminologiji — one su generičke i ponovo upotrebljive.

---

## 4. Infrastruktura — lokalni dev (Faza 0)

```
infra/
├── docker-compose.yml       # postgres:16, redis:7, minio, backend, frontend
├── postgres/
│   └── init-rls.sql         # Bootstrap RLS role (app_user bez BYPASSRLS)
└── minio/
    └── bucket-policy.json
```

`docker-compose.yml` diže cijelo Fazu 0 okruženje jednom komandom — nijedan agent ne razvija protiv "zamišljene" baze, uvijek protiv iste lokalne instance koju svi dijele.

---

## 5. API kontrakt — ko određuje granicu Backend/Frontend

Prije nego što Backend i Frontend agent počnu paralelno (Sekcija 8.9), **Chief Architect agent** piše minimalan OpenAPI/tipski kontrakt za Fazu 0+1 endpoint-e (institutions, auth, self-assessments, subcriteria-scores) u `docs/api-contract-v1.md`. FastAPI automatski generiše OpenAPI šemu iz koda — ali za prvi prolaz, kontrakt se piše RUČNO prije koda, da Frontend agent ne čeka da Backend agent završi da bi počeo raditi na wizard komponentama.

---

## 6. Redosled gradnje temelja (šta prvo, doslovno)

1. `infra/docker-compose.yml` + `postgres/init-rls.sql` — svi imaju isto okruženje.
2. `backend/src/caf/core/config.py` + `db/session.py` + `db/base.py` — skeleton bez modela.
3. `docs/api-contract-v1.md` — Arhitekta piše kontrakt za Fazu 0+1.
4. Backend: modeli → schemas → RLS politike + `check_approved_sar_lock` trigger → Alembic migracija → testovi (RLS + lock testovi PRVI, prije servisa).
5. Backend: servisi → routeri, prateći kontrakt iz koraka 3.
6. Frontend: `i18n/` setup + `app/[locale]/layout.tsx` + `lib/api-client.ts` skeleton (paralelno sa korakom 4, jer kontrakt već postoji).
7. Frontend: `features/auth` → `features/wizard` (konzumira endpoint-e iz koraka 5).
8. QA agent: end-to-end test cijelog toka (login → wizard unos → Approved Lock) na oba jezika, tek kad 4–7 stoje.

**Ovo je temelj.** Ništa iz Faze 1 (dashboard, CIP, konsenzus AI) se ne počinje dok koraci 1–3 nisu na mjestu — inače gradimo krov prije zidova.
