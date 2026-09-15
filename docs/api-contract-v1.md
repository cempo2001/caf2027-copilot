# API Contract v1 — CAF 2027 Copilot (Faza 0 + Faza 1)

Vlasnik: Chief Architect Agent (CLAUDE.md Sekcija 7.1). Piše se RUČNO, prije modela/servisa (docs/ARCHITECTURE.md, Sekcija 6, korak 3) — Frontend agent gradi protiv ovog kontrakta bez čekanja na gotov Backend kod. FastAPI će kasnije generisati stvaran OpenAPI iz koda; ovaj dokument je izvor istine dok se kod ne napiše, i mora ostati sinhronizovan (izmjena kontrakta = izmjena ovog fajla PRVO).

Sve rute su prefiksovane sa `/api/v1`. Sve rute (osim `/auth/login`) zahtijevaju `Authorization: Bearer <jwt>`.

---

## 1. Konvencije (važe za sve endpoint-e)

### 1.1 Jezik (CLAUDE.md Sekcija 6)

Jezik dolazi iz JWT `lang` claim-a (postavljen pri loginu, vidi 2.1). Svaki error odgovor je lokalizovan na taj jezik. Frontend ne šalje `Accept-Language` za autentifikovane rute — jezik je već u tokenu.

### 1.2 Format greške (standardan za sve endpoint-e)

```json
{
  "error": "sar_locked",
  "message": "Samoprocjena je odobrena i trajno zaključana — izmjena nije moguća."
}
```

`error` je stabilan mašinski ključ (vidi `caf.core.i18n._MESSAGES`), `message` je lokalizovan tekst. Frontend prikazuje `message` direktno korisniku, koristi `error` za programsku logiku (npr. disable dugme kad je `sar_locked`).

### 1.3 Status kodovi (CLAUDE.md Sekcija 3, pravilo 3)

| Kod | Značenje | Primjer |
|---|---|---|
| 200/201 | Uspjeh | — |
| 401 | Nevalidan/istekao token | `invalid_token`, `invalid_credentials` |
| 403 | Tenant mismatch — pristup van sopstvene institucije | `tenant_mismatch` |
| 404 | Resurs ne postoji (ili nije vidljiv zbog RLS — namjerno se ne razlikuje od "ne postoji", da se ne otkrije postojanje tuđih podataka) | — |
| 409 | Approved Lock — pokušaj izmjene odobrenog SAR-a | `sar_locked` |
| 422 | Validacija (Pydantic) | standardni FastAPI validation error format |
| 503 | AI provider nedostupan (odgovor se SVEJEDNO vraća, sa fallback rezultatom — vidi 4.2) | `ai_provider_unavailable` (kao warning header, ne blokira odgovor) |

### 1.4 Paginacija (liste)

```json
{ "items": [...], "total": 42, "page": 1, "page_size": 20 }
```

---

## 2. Auth

### 2.1 `POST /api/v1/auth/login`

Jedina ruta bez JWT-a. Ne postavlja RLS kontekst (nema ga još).

**Request:**
```json
{ "email": "string", "password": "string", "lang": "me" }
```
`lang` je eksplicitan izbor korisnika na login ekranu (CLAUDE.md Sekcija 6.2 — jezik nije pretpostavljen default) — postaje trajni claim u tokenu do sledećeg logina.

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "string",
    "role": "sponsor | caf_lead | cae_team_member | employee",
    "institution_id": "uuid",
    "lang": "me | en"
  }
}
```

**Errors:** `401 invalid_credentials`.

---

## 3. Institutions

### 3.1 `GET /api/v1/institutions/me`

Vraća instituciju ulogovanog korisnika (iz `institution_id` JWT claim-a — RLS to automatski ograničava, endpoint ne prima institution_id kao parametar).

**Response 200:**
```json
{
  "id": "uuid",
  "name_me": "string",
  "name_en": "string",
  "sag_members_count": 12,
  "maturity_status": "in_progress | caf_user | null"
}
```

**Errors:** `404` (ne bi se trebalo desiti za ulogovanog korisnika — signal bug-a ako se desi).

---

## 4. Self-Assessments (SAR)

### 4.1 `GET /api/v1/self-assessments`

Lista SAR-ova institucije (obično jedan aktivan + istorija). RLS ograničava na `institution_id` iz tokena.

**Response 200:** paginirana lista:
```json
{
  "items": [
    { "id": "uuid", "status": "draft | submitted | approved", "created_at": "iso8601", "approved_at": "iso8601 | null" }
  ],
  "total": 1, "page": 1, "page_size": 20
}
```

### 4.2 `POST /api/v1/self-assessments`

Kreira novi SAR (`status: draft`). Samo `CAFLead` i `Sponsor` role.

**Response 201:** kao stavka iz 4.1.

**Errors:** `403 insufficient_role` ako rola nije CAFLead/Sponsor.

### 4.3 `GET /api/v1/self-assessments/{sar_id}`

Detalji SAR-a sa svih 28 podkriterijuma.

**Response 200:**
```json
{
  "id": "uuid",
  "status": "draft | submitted | approved",
  "approved_at": "iso8601 | null",
  "approved_by": "uuid | null",
  "subcriteria_scores": [
    {
      "subcriteria_code": "1.1",
      "criterion_number": 1,
      "name_me": "string", "name_en": "string",
      "score": 1,
      "evidence_text": "string",
      "weaknesses_text": "string",
      "quality_flag": "ok | too_short | too_generic | null"
    }
  ]
}
```

**Errors:** `404 not_found` (ne postoji ILI pripada drugoj instituciji — RLS ga ne prikazuje; namjerno isti odgovor, vidi 1.3).

### 4.4 `PATCH /api/v1/self-assessments/{sar_id}/subcriteria/{code}`

Ažurira jedan podkriterijum (Guided Wizard korak). **KRITIČNA RUTA** — mora provjeriti Approved Lock prije upisa (CLAUDE.md Sekcija 3, pravilo 3 — `check_approved_sar_lock` na nivou baze je zadnja linija odbrane, ali servisni sloj mora vratiti čist 409 prije nego što upit uopšte stigne do triggera).

**Request:**
```json
{ "evidence_text": "string", "weaknesses_text": "string", "score": 3 }
```

**Response 200:** ažurirana stavka podkriterijuma (kao u 4.3).

**Errors:**
- `409 sar_locked` — SAR je odobren (Approved Lock).
- `422` — score van opsega (1–5); `422 unknown_subcriteria` — šifra nije u CAF okviru.
- `403 insufficient_role` — Employee rola ne mijenja ocjene.
- `404 not_found` — tuđi ili nepostojeći SAR.

### 4.5 `POST /api/v1/self-assessments/{sar_id}/subcriteria/{code}/ai-consensus`

Poziva AI/Consensus Engine za predlog ocjene na osnovu unesenog teksta. **Vraća 200 čak i kad AI provider padne** — tada je `source: "fallback"` i status 503 dolazi kao header (`X-Consensus-Warning: ai_provider_unavailable`), ne kao HTTP greška koja blokira tok (CLAUDE.md Sekcija 6.2 — Offline Math Fallback je obavezan, ne opcioni error state).

**Response 200:**
```json
{
  "suggested_score": 3,
  "suggested_summary_text": "string",
  "source": "ai | fallback",
  "requires_human_confirmation": true
}
```

Frontend MORA prikazati ovo kao predlog koji korisnik eksplicitno potvrđuje (human-in-the-loop, CLAUDE.md Sekcija 7.5) — ne upisuje se automatski u 4.4.

### 4.6 `POST /api/v1/self-assessments/{sar_id}/approve`

Approved Lock — samo `Sponsor` rola. Nepovratna akcija.

**Response 200:**
```json
{ "id": "uuid", "status": "approved", "approved_at": "iso8601", "approved_by": "uuid" }
```

**Errors:**
- `409 sar_locked` — već odobren (idempotentnost: drugi poziv na već odobren SAR je greška, ne no-op — sprečava zabunu oko toga ko je "zaista" odobrio).
- `403 insufficient_role` — rola nije Sponsor.
- `403 sar_incomplete` — nisu sva 28 podkriterijuma ocijenjena.

---

## 5. CIP Akcioni plan (2x2 matrica)

### 5.1 `GET /api/v1/self-assessments/{sar_id}/cip`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title_me": "string", "title_en": "string",
      "quadrant": "quick_win | strategic | fill_in | reconsider",
      "as_is": "string", "to_be": "string",
      "status": "planned | in_progress | done"
    }
  ]
}
```

### 5.2 `POST /api/v1/self-assessments/{sar_id}/cip`

Kreira CIP stavku. Vraća 409 ako je roditeljski SAR zaključan (CIP se ne mijenja poslije Approved Lock-a u Fazi 1 — reviziju CIP-a posle zaključavanja rešava Faza 6+, van obima sada).

---

## 6. Evidence (dokazi, MinIO)

### 6.1 `POST /api/v1/self-assessments/{sar_id}/subcriteria/{code}/evidence`

Multipart upload. Vault & Documents agent (CLAUDE.md Sekcija 7.6).

**Response 201:**
```json
{ "id": "uuid", "filename": "string", "sha256": "string", "av_scan_status": "clean | infected | pending" }
```

**Errors:** `409 sar_locked`, `422` ako fajl ne prođe ClamAV sken (`av_scan_status: infected` — fajl se NE čuva, odbija se odmah, ne tiho zanemaruje).

---

## 7. Šta NIJE u v1 kontraktu (namjerno)

Rute za Nivo 2 (Government View), Nivo 3 (EFA/CER) i Nivo 4 (EIPA export) se ne definišu ovdje — dolaze kao `api-contract-v2.md` kad Faza 2/3 stvarno počne (CLAUDE.md Sekcija 4.0). Dodavanje ruta ovdje prije nego što faza počne je širenje obima bez odobrenja Team Lead-a.
