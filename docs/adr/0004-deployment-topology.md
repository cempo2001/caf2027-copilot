# ADR-0004: Distribuciona topologija — on-prem i cloud iz istog koda

- **Status:** Prihvaćeno
- **Datum:** 2026-09-16
- **Kontekst:** CLAUDE.md Sekcija 4 (četvorostepena multi-tenant hijerarhija), ADR-0001 (RLS tenant izolacija)

## Kontekst

Platforma se ne prodaje kao jedna SaaS instanca. Svaka institucija koja je
nabavi bira gdje se instalira:

1. **On-prem** — instalacija na serveru same institucije (npr. interni
   server Ministarstva), potpuno odvojena infrastruktura (Postgres, MinIO,
   Redis, ClamAV) koju drži i njome upravlja ta institucija.
2. **Cloud** — hostovana instanca (jedna ili više institucija dijele
   infrastrukturu, izolovane RLS-om na nivou baze — isti mehanizam koji već
   koristimo za Nivo 1/2 razdvajanje).

Ovo nije bilo eksplicitno riješeno do sada; CI/CD odluka je bila blokirana
dok se ne razjasni da li gradimo jedan deployment target ili dva.

## Odluka

**Jedan kod, dva profila deploymenta — nema grananja aplikativne logike po
okruženju.**

- RLS tenant izolacija (ADR-0001) ostaje uključena u oba profila. Kod
  on-prem instalacije postoji samo jedna institucija u bazi — RLS mehanizam
  je i dalje aktivan, samo nema drugog tenant-a od kojeg bi izolovao.
  Ovo znači da ne pravimo poseban "single-tenant mod" — izbjegavamo dupliranje
  logike i rizik da jedan mod dobije sigurnosnu zakrpu koju drugi promaši.
- Paketovanje ostaje kontejnerizovano (Docker slike za backend, frontend,
  migracije) — isto za oba profila.
- **On-prem isporuka:** `docker-compose.yml` (već postoji u repou) +
  instalacioni skript koji generiše `.env` (JWT secret, MinIO kredencijali,
  DB lozinka) pri prvoj instalaciji. Cilj: IT tim institucije treba da
  pokrene 1-2 komande, ne da upravlja Kubernetes klasterom.
- **Cloud isporuka:** iste slike, orkestracija preko Docker Swarm-a (već
  planirano za Redis 7 Blackboard orkestraciju u CLAUDE.md stack-u — ne
  uvodimo Kubernetes kao treći sistem samo za cloud profil).
- **Container registry** je tačka spajanja: CI gradi slike jednom po
  git tag-u/release-u, oba profila (on-prem instalacioni skript i cloud
  deployment) povlače iz istog registry-ja po verzionisanom tag-u
  (npr. `caf2027-backend:1.4.0`), nikad `:latest` u produkciji.

## Otvoreno (namjerno odloženo, CLAUDE.md 7.9 — ne blokira Fazu 1)

- **Air-gapped/offline instalacija:** nije još potvrđeno da li neka
  institucija zahtijeva instalaciju bez internet pristupa. Ako da, treba
  dodatni CI korak koji pravi `.tar` izvoz svih slika za ručni prenos.
  Odluka odložena do prvog konkretnog zahtjeva (Team Lead odluka, 16.9.2026).
- **Git/CI hosting:** odlučeno da se za sada radi lokalno (bez git remote-a,
  bez CI-ja) dok se ne odredi prvi kupac/institucija. Kada se odredi, CI
  pipeline (build slika + testovi na svaki push) je sledeći korak i ne
  zavisi od ove odluke — može se dodati naknadno bez izmjene arhitekture.
- **Update/verzionisanje on-prem instanci:** treba definisati proces kojim
  institucija ažurira svoju on-prem instalaciju (migracije baze moraju biti
  strogo uzlazne i kompatibilne — već pravilo iz ARCHITECTURE.md) — nije
  hitno za Fazu 1, jer još nema on-prem instance u produkciji.

## Posljedice

- Nema promjene u postojećem kodu Faze 1 (CIP, Evidence, AI Consensus) —
  ova odluka utiče samo na DevOps/CI sloj koji tek treba da se gradi.
- `docker-compose.yml` i `.env.example` ostaju izvor istine i za on-prem i
  za cloud konfiguraciju; ne pravimo poseban compose fajl po profilu dok se
  ne pojavi konkretna razlika (npr. TLS terminacija na cloud load balanceru
  nasuprot on-prem reverse proxy-ju institucije).
