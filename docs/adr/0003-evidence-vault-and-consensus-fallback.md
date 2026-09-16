# ADR-0003: Dokazni trezor (fail-closed AV) i Offline Math Fallback za predlog ocjene

- **Status:** Prihvaćeno (Faza 1, 16.9.2026)
- **Vlasnici:** Vault & Documents Agent (7.6), AI/Consensus Engine Agent (7.5); review: Database & Security (7.2)

## Kontekst

api-contract-v1.md je za 4.5, 5.2 i 6.1 ostavio otvorena pitanja (tijelo CIP zahtjeva, ime multipart polja, ponašanje kad AV nije dostupan, šta tačno radi "matematički fallback" kad model ima jednu ocjenu po podkriterijumu). Kontrakt je dopunjen 16.9.2026; ovaj ADR bilježi razloge.

## Odluke

1. **Nove tenant tabele `cip_items` i `evidence_files`** (migracija 0004) prate ADR-0001 bez izuzetka: denormalizovan `institution_id` + kompozitni FK, ENABLE/FORCE RLS sa `NULLIF` politikom, GRANT za `app_user`. `check_approved_sar_lock()` je proširen na obje tabele — isti 409 kao za ocjene. SQL je provjeren na Postgres 16 kao `app_user` (RLS, kompozitni FK, lock na INSERT/UPDATE/DELETE, downgrade funkcije).

2. **AV skeniranje je fail-closed.** clamd (INSTREAM preko TCP-a, sopstveni mali klijent bez nove zavisnosti) — skener nedostupan => 503, fajl se ne čuva; prijetnja => 422, fajl se ne čuva, a `infected` nije dozvoljena vrijednost ni u bazi (CHECK). Jedini izuzetak je `AV_SCAN_MODE=disabled` za lokalni razvoj (status `pending`); `Settings` odbija start sa tim podešavanjem kad je `ENVIRONMENT=production` (isto važi za MinIO bez TLS-a).
   - Odbačeno: čuvanje u karantin i kasnije skeniranje — zahtijeva worker i red poslova kojih u Fazi 1 nema, a do skeniranja bi "dokaz" postojao bez verifikacije.

3. **Tip fajla se ne vjeruje klijentu.** Dozvoljena lista ekstenzija + provjera "magic" bajtova; sačuvani content-type je naš. Ključ objekta u MinIO je `{institution}/{sar}/{kod}/{uuid}` — bez korisničkog imena fajla. Ako upis u bazu padne poslije uploada (npr. Approved Lock u međuvremenu), objekat se briše.

4. **Offline Math Fallback = PDCA prosjek iz teksta dokaza.** Model podataka ima jednu ocjenu po podkriterijumu (nema pojedinačnih ocjena članova SAG-a), pa "aritmetička sredina PDCA ocjena" znači: svaka PDCA faza (Enableri) odnosno dimenzija mjerenje/trend/cilj/poređenje (Rezultati) dobija 1–5 prema broju prepoznatih indikatora u sačuvanom tekstu, predlog je zaokružena sredina, kratak dokaz (<20 riječi) ograničava predlog na 2. Liste indikatora su posebne za `me` i `en` i biraju se po jeziku UNOSA; oznake u objašnjenju su na jeziku SESIJE; citat korisnika se ne prevodi (CLAUDE.md 6.1). Deterministički, stdlib-only, testiran bez mreže.
   - Ograničenje: ovo je heuristika pokrivenosti PDCA elemenata u tekstu, ne procjena kvaliteta. Zato je predlog uvijek human-in-the-loop, a objašnjenje (`breakdown`) se vraća uz njega.

5. **AI provajder nije izabran.** Postoji samo interfejs (`ScoreSuggestionProvider`); `build_ai_provider` vraća `None` dok Team Lead ne odobri stvaran model (CLAUDE.md Sekcija 2). Svaki odgovor je zato `source: "fallback"` sa `X-Consensus-Warning`. Provajderova greška ili nevalidan odgovor (ocjena van 1–5, prazan tekst) takođe vode u fallback.

6. **Prihvatanje predloga na frontendu mijenja samo ocjenu.** Objašnjenje se ne lijepi u tekst dokaza — inače bi sistemski tekst postao "korisnikov dokaz" i naduvao sledeći fallback predlog.

## Posljedice

- Lokalni `docker compose` dobija `clamav` servis (≈3–4 GB RAM-a, prvi start nekoliko minuta).
- Next.js `serverActions.bodySizeLimit` je 26 MB (upload ide kroz Server Action).
- Faza 5: MinIO servisni nalog sa pravima samo na `caf-evidence` bucket umjesto root naloga; `MINIO_SECURE=true`.
