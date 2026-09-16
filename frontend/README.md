# Frontend — CAF 2027 Copilot

Next.js 15 (App Router, RSC, Server Actions), React 19, Tailwind CSS v4, next-intl.
Struktura i pravila slojeva: `docs/ARCHITECTURE.md` Sekcija 3. API kontrakt koji ovaj
frontend konzumira: `docs/api-contract-v1.md`.

## Lokalni development

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000 — redirektuje na /me/login ili /en/login
```

Backend mora raditi na `http://localhost:8765` (vidi root `README.md` i
`docker-compose.yml`) — `NEXT_PUBLIC_API_URL` u `.env` određuje bazu (default
`http://localhost:8765` ako nije postavljen).

Test nalozi za login (posle `python scripts/seed_dev.py` u `backend/`):
`sponsor@test.caf`, `lead@test.caf`, `member@test.caf`, `employee@test.caf`,
lozinka `Caf2027!`.

## Struktura

- `src/app/[locale]/` — rute, locale prefiks `/me` ili `/en` je obavezan (CLAUDE.md 6.2)
- `src/features/*/actions.ts` — jedino mjesto koje zove backend (Server Actions)
- `src/components/ui/` — generičke primitive, bez CAF poslovne logike
- `src/lib/api-client.ts` — tipizovan fetch wrapper, standardni error format
- `src/lib/auth.ts` — httpOnly session cookie (JWT se ne dodiruje na klijentu)
- `src/i18n/` — next-intl routing/middleware/poruke (sr-ME, en-US)

## Status (Faza 1)

- [x] App Router skeleton + `[locale]` rutiranje (next-intl)
- [x] Svijetla/tamna tema
- [x] `lib/api-client.ts` protiv `docs/api-contract-v1.md`
- [x] `features/auth` — login/logout, httpOnly session cookie, role-gated route group
- [ ] `features/wizard` — Vođeni Čarobnjak (9 kriterijuma / 28 podkriterijuma) — sledeći modul
- [ ] `features/sar`, `features/cip` — pregled SAR-a, 2x2 CIP matrica
- [ ] MinIO evidence upload UI
