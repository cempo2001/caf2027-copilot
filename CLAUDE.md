# CLAUDE.md — CAF 2027 Copilot

Ovaj dokument je **stalna vodilja** za razvoj sistema CAF 2027 Copilot u Claude Code (najnovija verzija, specijalizovana za izradu aplikacija). Svaka sesija razvoja počinje sa ovim fajlom kao izvorom istine o arhitekturi, obimu, fazama i pravilima rada. Ne odstupa se od njega bez eksplicitne odluke Danila (vlasnika projekta) ili donosioca odluka.

---

## 0. Status i identitet projekta

- **Naziv:** CAF 2027 Copilot — Digital Excellence Ecosystem
- **Ovo je ZASEBAN, nezavisan projekat.** Nije nastavak, nadogradnja niti migracija postojećeg "CAF 2026 Copilot" sistema (React/Vite/Gemini, u produkciji, ugovor sa Ministarstvom javne uprave). Ta dva sistema se **ne mešaju**: nema deljenog koda, nema deljene baze, nema migracije podataka između njih. CAF 2026 Copilot nastavlja svoj život nezavisno.
- **Cilj operativnosti:** sistem mora biti u produkciji (deployovan i operativan) **najkasnije do februara 2027. godine.** Ovo je tvrd rok (hard deadline), ne orijentacioni. Vidi Sekciju 4.0 za posledice ovog roka po obim.
- **Model rada:** projekat prolazi kroz jasno definisane faze (vidi Sekciju 4). Tek nakon što je sistem deployovan i operativan, dalje promjene i proširenja rade se **na zahtjev donosilaca odluka** (Vlada, MJU, EIPA, Sponzor institucije) — ne unapred, ne po pretpostavci šta bi moglo zatrebati.
- **Ovaj fajl se ažurira** kad god donosilac odluka promeni obim, prioritet ili arhitektonsku odluku. Svaka takva promjena mora biti zapisana ovde sa datumom, pre nego što se odrazi u kodu.

---

## 1. Misija i metodološki okvir

CAF 2027 Copilot digitalizuje proces samoprocjene javne uprave po evropskom CAF 2020/2026 okviru i podržava napredovanje ka **CAF Excellence Recognition (CER 2025)** — standardu Evropskog resursnog centra za CAF pri EIPA-i (Mastriht).

Platforma prati **4-nivoa hijerarhiju**, ali (vidi Sekciju 4) **ne gradimo sva 4 nivoa odjednom niti u punom obimu iz starta**:

1. **Nivo 1 — Institucija / organ javne uprave (Local).** Operativno sprovođenje samoprocjene (SAR): SAG tim (5–20 članova), uloge Sponsor/CAFLead/CAETeamMember/Employee, Vođeni Čarobnjak za 9 kriterijuma / 28 podkriterijuma, dualni konsenzus engine (AI + Offline Math Fallback), CIP akcioni plan (2x2 matrica Quick Wins / Strateški), Approved Lock (trajno zaključavanje odobrenog SAR-a na nivou baze).
2. **Nivo 2 — Država / Vlada Crne Gore (National).** Government View benchmarking svih organa, Nacionalni CAF Indeks Zrelosti (0–100), izdavanje statusa "CAF User".
3. **Nivo 3 — EFA Audit Portal (CER sertifikacija).** Portal za eksterne ocjenjivače: 3 stuba (proces samoprocjene, sprovođenje akcionog plana, TQM zrelost/8 principa), nivoi CER*/**/***, generisanje zvaničnog CER izvještaja.
4. **Nivo 4 — EIPA / EUPAN (Pan-European, Mastriht).** Ovo je **integraciona tačka**, ne nešto što mi gradimo ili kontrolišemo — vidi napomenu u Sekciji 4.4.

---

## 2. Tehnički stack (obavezujući, ne mijenjati bez eksplicitnog dogovora)

| Sloj | Tehnologija |
|---|---|
| Frontend | Next.js 15 (App Router, RSC, Server Actions), React 19, Tailwind CSS v4, Shadcn UI |
| Vizuelizacija | Recharts, Tremor, Nivo.rocks (radar spidogrami, 2x2 matrice) |
| Backend API | FastAPI (Python 3.12+, async SQLAlchemy 2.0, Pydantic v2.10+) |
| Baza podataka | PostgreSQL 16/17, native Row Level Security (RLS) |
| Cache / orkestracija agenata | Redis 7 (pub/sub, state checkpointing) |
| Dokazni trezor | MinIO S3, SHA-256 potpis, ClamAV antivirus sken |
| AI orkestracija | Hibridni LLM engine + obavezni 100% lokalni matematički fallback (aritmetička sredina PDCA ocjena + spajanje teksta), za rad bez interneta |
| Auth | JWT sa custom claims, tajne isključivo preko `.env` (Pydantic BaseSettings) |

**Napomena o Go mikroservisu:** originalna specifikacija je predviđala poseban Go servis za auth/API Gateway. **Ne uvodimo drugi backend jezik od starta.** JWT auth i API Gateway rade u FastAPI-ju u Fazi 1–2. Go servis se razmatra tek ako se izmjeri stvaran throughput problem koji FastAPI ne rešava — to je odluka za kasniju fazu, ne pretpostavka.

**Napomena o AI modelima:** ne referenciramo nepostojeće/izmišljene nazive modela (npr. "GPT-6", "Gemini 3.1 Pro" — ovi ne postoje). Konkretan LLM provajder i model biraju se u Fazi 1 prema tada dostupnim, verifikovanim, produkcijski podržanim modelima, i upisuju se ovde kad se odluka donese.

---

## 3. Inženjerska pravila (važe za svaki commit)

1. Piši kao Principal Software Architect: čist, modularan, kompajlabilan, produkcijski kod. Nema placeholder/TODO koda u kodu koji se predstavlja kao gotov.
2. **Zabranjen monolitski kod u jednom fajlu.** Uvijek razdvoji slojeve: API Router → Service Layer → ORM Model → Pydantic Schema/DTO. Isto važi za frontend: komponente, server actions i data-fetching logika se ne mešaju u jednom fajlu.
3. **Obavezno hendlovanje edge-case grešaka:** HTTP 409 (izmjena odobrenog SAR-a), 401/403 (RLS/auth narušavanja), 422 (validacija), 503 (AI provider nedostupan → fallback).
4. **Security by Design:** nema hardkodovanih tajni. Sve preko `.env` / Pydantic BaseSettings. JWT sa custom claims za tenant/rolu. Svaka tvrdnja o bezbjednosti mora biti provjerljiva (threat model, ne marketinški izraz tipa "neprobojno").
5. **Rad sekvencijalno, po modulima.** Prije početka svakog modula: najavi šta se gradi, na koji dio arhitekture i faze se odnosi, i potvrdi usklađenost sa CER 2025 standardom gdje je relevantno.
6. **Testiranje nije opciono.** Svaki servisni sloj koji dotiče Approved Lock, RLS izolaciju ili konsenzus ocjenjivanje mora imati testove prije nego što se modul smatra završenim.
7. **Nema migracije sa CAF 2026 Copilot-a.** Ne pišemo import skripte, ne dijelimo šeme baze, ne referenciramo taj kod. Ako je u budućnosti donesena odluka da se podaci prenesu, to je posebna, eksplicitno naručena faza — van obima ovog dokumenta dok se ne zapiše ovdje.

---

## 4. Fazni plan (deploy najkasnije februar 2027.)

Cilj faznog plana: svaka faza proizvodi nešto što se može pokazati i testirati, bez preuranjenog uvođenja kompleksnosti (drugi jezik, pan-evropska integracija) prije nego što je stvarno potrebna.

### 4.0 Realnost roka — pročitati prije planiranja bilo kog sprinta

Rok je februar 2027. Danas je septembar 2026 — to je **otprilike 5 mjeseci** do deploy-a, ne godina i po kako je prvobitno planirano. Ovo materijalno mijenja šta je realno izgraditi do roka, i to mora biti jasno rečeno, ne prećutano:

- **Fazu 0 + Faza 1 (Nivo 1 — Institucija, SAR samoprocjena) je ono što je realno ambiciozno ali izvodljivo do februara 2027**, uz disciplinovan rad i bez širenja obima usput. Ovo je i najvrijedniji dio za korisnike — kompletan digitalni SAR proces za jednu ili više institucija.
- **Faza 2 (Government View), Faza 3 (EFA/CER portal) i Faza 4 (EIPA integraciona spremnost) realno ne staju u ovaj rok** ako se rade sa istim nivoom kvaliteta, testiranja i bezbjednosti kao Faza 0/1. Guranje svih 6 faza u 5 mjeseci vodi ili u prekovremeni "brzi" kod bez testova (kрши pravila iz Sekcije 3), ili u kašnjenje koje ugrožava sam februarski rok.
- **Preporuka (za tvoju odluku, ne automatska promjena):** deploy u februaru 2027 pokriva Fazu 0 + Fazu 1, potpuno dvojezično (Sekcija 6), potpuno testirano i bezbjedno. Faze 2–4 se planiraju kao **Faza 6+ rad na zahtjev donosilaca odluka**, posle februara — što se uklapa i sa tvojim ranijim pravilom da se posle deploy-a dalje radi na zahtjev, ne unaprijed.
- **Ako donosilac odluka insistira da sve 4 nivoa budu u produkciji do februara**, to mora biti eksplicitna odluka koju ti unosiš ovdje sa datumom — jer tada pravila iz Sekcije 3 (testiranje, slojevita arhitektura, security review) moraju ili popustiti (rizično) ili se mora dodati tim/budžet van trenutnog CAPEX-a iz sažetka. Ne guram ovu odluku pod tepih — eskalira se tebi.

**Dok se ne zapiše drugačija odluka ovdje, radni okvir je: deploy februar 2027 = Faza 0 + Faza 1, potpuno gotove i produkcijski spremne.**

### Faza 0 — Temelji (baza, auth, tenant izolacija)
- PostgreSQL šema: `institutions`, `users` (uloge), `self_assessments`, `subcriteria_scores`.
- RLS politike za tenant izolaciju po `institution_id`.
- SQL trigger `check_approved_sar_lock` (blokira izmjenu odobrenog SAR-a → 409 na API sloju).
- FastAPI skeleton: Router/Service/ORM/DTO slojevi, JWT auth sa custom claims.
- Alembic migracije, osnovni test suite (pytest + testcontainers za RLS scenarije).
- **Izlaz faze:** radna baza + auth, bez UI-ja, potpuno pokrivena testovima za RLS i Approved Lock.

### Faza 1 — Nivo 1: Institucija (SAR samoprocjena)
- Next.js 15 frontend: Vođeni Čarobnjak (28 podkriterijuma), role-based UI (Employee/CAETeamMember/CAFLead/Sponsor).
- Dualni konsenzus engine: AI predlog ocjene + obavezni Offline Math Fallback.
- CIP akcioni plan (2x2 matrica).
- MinIO integracija za dokaze (SHA-256 potpis, ClamAV sken).
- Dvojezičnost sr-ME / en-US, svijetla/tamna tema.
- **Izlaz faze:** jedna institucija može kompletno sprovesti SAR proces od unosa do Approved Lock-a.

### Faza 2 — Nivo 2: Državni pregled (Government View)
- Agregacija podataka preko institucija (i dalje strogo RLS-izolovano po tenantu, agregacija samo na dozvoljenom nivou pristupa).
- Government View dashboard za MJU/Nacionalnog organizatora: benchmarking, Nacionalni CAF Indeks Zrelosti (0–100).
- Izdavanje statusa "CAF User".
- **Izlaz faze:** Vlada/MJU vidi zrelost svih uključenih institucija na jednom mjestu.

### Faza 3 — Nivo 3: EFA Audit Portal (CER sertifikacija)
- Portal za eksterne ocjenjivače (EFA) i Nacionalnog organizatora.
- 3 stuba ocjenjivanja, skala 1–5, podrška za CER*/**/*** (uslov: prethodni CER* za više nivoe, min. 2 eksterna ocjenjivača za CER**/***).
- Generisanje zvaničnog CER izvještaja/sertifikata.
- **Izlaz faze:** institucija može proći kompletan CER proces kroz platformu, sa izveštajem spremnim za EIPA standard.

### Faza 4 — Integraciona spremnost (Nivo 4 / EIPA)
Ovo **nije** faza u kojoj gradimo pan-evropsku infrastrukturu — nemamo mandat niti razlog da gradimo/hostujemo bilo šta za EIPA. Ova faza znači:
- Export/API format usklađen sa onim što EIPA/EUPAN registar očekuje (ako i kada takva integracija bude tražena).
- Dokumentacija spremnosti za povezivanje, ne stvarna implementacija dashboard-a u Mastrihtu.
- **Izlaz faze:** sistem je "integracije spreman", odluku o stvarnom povezivanju donosi EIPA/nadležni organ, ne mi.

### Faza 5 — Deploy i operativni start (cilj: najkasnije februar 2027., obim = Faza 0 + Faza 1 dok se ne odluči drugačije — vidi Sekciju 4.0)
- Produkcioni deployment (infrastruktura, CI/CD, monitoring/observability, backup/DR plan).
- UAT sa stvarnim korisnicima (SAG tim, Sponzor, MJU).
- Sigurnosna revizija (penetration test / eksterni security review) prije puštanja u rad.
- **Izlaz faze:** sistem je operativan i u produkcionoj upotrebi.

### Faza 6+ — Promjene na zahtjev donosilaca odluka
Nakon Faze 5, sistem se **ne mijenja proaktivno**. Svaka nova funkcionalnost, proširenje ili izmjena arhitekture pokreće se **isključivo na eksplicitan zahtjev donosilaca odluka** (Vlada, MJU, Sponzor institucije, EIPA). Svaki takav zahtjev:
1. Zapisuje se ovde (datum, ko traži, šta traži).
2. Prolazi kroz istu inženjersku disciplinu kao i inicijalne faze (moduli, slojevi, testovi).
3. Ne otvara automatski vrata za dodatne "nice to have" promjene van onoga što je zatraženo.

---

## 5. Šta eksplicitno NIJE u obimu (dok se ne zapiše ovdje drugačije)

- Migracija ili sinhronizacija podataka sa CAF 2026 Copilot sistemom.
- Go mikroservis za auth (dok se ne pokaže stvarna potreba).
- Stvarna implementacija/hostovanje pan-evropskog EIPA/EUPAN dashboard-a.
- Bilo kakvo proširenje na sektor obrazovanja (CAF in Education) — ostaje samo kao referentni materijal dok se ne zatraži.

---

## 6. Internacionalizacija (i18n) — obavezujući zahtjev, ne kozmetika

Aplikacija se gradi **od Faze 0 nadalje** kao potpuno dvojezična: **crnogorski (sr-ME / me-ME) i engleski (en-US)**. Ovo nije "dodaj prevod na kraju" — jezik je parametar koji utiče na ponašanje sistema, ne samo na prikaz teksta. Pravilo: **sve što aplikacija radi, radi u oba jezika podjednako potpuno; izabrani jezik određuje na kom jeziku se odvijaju svi procesi za tog korisnika/tu sesiju, ne samo labele na ekranu.**

### 6.1 Šta znači "kompatibilnost u potpunosti"

- **UI sloj:** svaki string u interfejsu (labele, dugmad, poruke o greškama, validacije, email/notifikacije, PDF izvještaji, CER sertifikati) postoji u oba jezika — nema hardkodovanog teksta ni na jednom jeziku direktno u komponentama.
- **Podaci koje unosi korisnik** (Slabosti, Dokazi, tekstualni odgovori u SAR-u) čuvaju se sa oznakom jezika na kom su uneseni — sistem ih ne prevodi automatski niti ih meša, ali zna na kom su jeziku radi ispravnog prikaza i AI obrade.
- **Generisani sadržaj** (AI predlozi ocjena, sažimanje teksta u konsenzus engine-u, automatski izvještaji za Ministra, CER izvještaj/sertifikat) generiše se **na jeziku koji je korisnik odabrao za tu sesiju** — AI/Consensus Engine agent prosleđuje izabrani jezik kao parametar u svaki poziv, ne generiše na jednom jeziku pa prevodi naknadno.
- **Offline Math Fallback** (spajanje teksta bez AI-ja) takođe poštuje jezik sesije — spaja/agregira tekstualne unose na jeziku na kom su uneseni, bez miješanja.
- **Validacija kvaliteta unosa** (indikatori za prekratke/formalne odgovore u Guided Wizard-u) radi na oba jezika podjednako — pravila za crnogorski nisu "engleska pravila prevedena", već posebno definisana gdje jezik to zahtijeva (dužina riječi, gramatika).
- **PDF/DOCX izvještaji i CER sertifikati** generišu se u verziji jezika sesije, sa ispravnim formatom datuma, brojeva i naziva uloga za taj jezik.
- **Dokumentacija, error poruke sa backend-a (FastAPI) i log poruke ka korisniku** (ne interni dev logovi) prate isti princip — backend vraća error kod + poruku lokalizovanu prema `Accept-Language` / eksplicitnom izboru korisnika, ne samo frontend prevodi statične stringove.

### 6.2 Tehnička implementacija (okvir, detalji se preciziraju u Fazi 0/1)

- Frontend: `next-intl` ili ekvivalentan App Router-kompatibilan i18n sloj; jezik je dio URL-a ili sesije, ne samo lokalnog state-a preglednika.
- Backend: jezik korisnika je deo JWT custom claims ili eksplicitnog request parametra; svaki servis koji generiše tekst (izvještaji, AI pozivi, notifikacije) prima taj parametar eksplicitno — ne pretpostavlja default.
- Baza: kolone za dvojezični statički sadržaj (npr. nazivi kriterijuma/podkriterijuma iz CAF okvira) modeluju se sa parovima `_me` / `_en` ili posebnom translation tabelom — Database agent bira pristup u Fazi 0 i to se ovde upisuje kad se odluči.
- AI/Consensus Engine agent: jezik je obavezan parametar prompta; nema "generiši pa prevedi" — to dupliramo troškove i unosi grešku.

### 6.3 Guardrail

Nijedan modul se ne smatra završenim (vidi Sekciju 3, pravilo 6 i Sekciju 7.7 — QA agent) ako radi ispravno samo na jednom jeziku. QA agent testira svaki kritični tok (Guided Wizard unos, Approved Lock, generisanje CER izvještaja) **u oba jezika** kao dio definicije "gotovo".

---

## 8. Tim: podela rada između AI agenata i tebe kao Team Lead-a

Razvoj u Claude Code vodi se kroz specijalizovane agente (subagente), svaki sa uskim mandatom. Ovo sprečava da se sve radi "iz jedne glave" bez provere, i drži disciplinu iz Sekcije 3. Agenti se pozivaju po potrebi modula (Sekcija 4) — ne rade svi paralelno na svemu.

### 7.0 Danilo — Team Lead / Product Owner (ti)

Ti nisi agent koji piše kod — ti si jedini kanal ka donosiocima odluka i konačna instanca odlučivanja. Tvoja uloga:

- **Definišeš i menjaš obim.** Samo ti (ili donosilac odluka preko tebe) možeš da promeniš ovaj CLAUDE.md — faze, prioritete, arhitektonske odluke (npr. da li uvodimo Go servis).
- **Odobravaš prelazak između faza.** Nijedan agent ne prelazi iz Faze 0 u Fazu 1 bez tvoje potvrde da je "Izlaz faze" stvarno ispunjen.
- **Prosleđuješ zahtjeve donosilaca odluka** (Vlada, MJU, EIPA, Sponzor) u konkretne, ograničene zadatke za agente — u Fazi 6+ ti si taj koji "prevodi" politički/institucionalni zahtjev u inženjerski tiket, tako da agenti ne dobijaju nejasne instrukcije direktno od trećih strana.
- **Radiš finalni review pred deploy** (uz Deployment agenta) — niko ne ide u produkciju bez tvog "da".
- **Čuvaš budžetsku i realnost-proveru.** Kad neki agent (posebno Arhitekta) predloži nešto što širi obim ili budžet, ti to ili odobravaš ili vraćaš na doradu — agenti ne donose tu odluku sami.

### 7.1 Chief Architect Agent

- **Mandat:** vlasnik arhitektonskih odluka i ovog CLAUDE.md fajla na tehničkom nivou. Piše i ažurira ADR-ove (Architecture Decision Records) za svaku veću odluku (npr. "zašto ne uvodimo Go servis u Fazi 0").
- **Radi:** definiše granice servisa, šemu multi-tenant izolacije, kontrakte između frontend/backend/AI slojeva, review svake nove faze pre nego što druga dva agenta počnu da pišu kod.
- **Ne radi:** ne piše produkcijski kod modula (to rade Backend/Frontend agenti) i ne odlučuje o obimu/budžetu — to eskalira tebi.
- **Alat/skill:** `engineering:architecture`, `engineering:system-design`.
- **Model:** **Opus 5.** Arhitektonske odluke se teško i skupo ispravljaju kasnije — ovdje cijena po tokenu nije faktor koji odlučuje.

### 7.2 Database & Security Agent (RLS / Approved Lock)

- **Mandat:** PostgreSQL šema, RLS politike, `check_approved_sar_lock` trigger, Alembic migracije, JWT/auth šema (custom claims).
- **Radi:** Faza 0 u celosti (baza + auth skeleton); u svakoj kasnijoj fazi, review svake nove tabele/upita zbog tenant izolacije.
- **Ne radi:** poslovnu logiku (Service Layer) — to je Backend agent; ne odlučuje o UI-ju.
- **Guardrail:** svaka nova tabela koja sadrži `institution_id` mora imati RLS politiku pre merge-a — bez izuzetka.
- **Model:** **Opus 5.** Najveći bezbjednosni rizik u cijelom sistemu (tenant izolacija, trajno zaključavanje podataka) — greška ovdje je najskuplja moguća greška.

### 7.3 Backend Agent (FastAPI Service Layer)

- **Mandat:** Router → Service → ORM → DTO slojevi u FastAPI-ju, edge-case error handling (409/401/403/422/503), konsenzus engine (AI + Offline Math Fallback) kao servisni modul.
- **Radi:** Faza 1 (SAR API, konsenzus, CIP), Faza 2 (agregacioni endpoint-i za Government View), Faza 3 (EFA/CER evaluacioni API).
- **Ne radi:** ne dira RLS politike direktno (traži od Database agenta), ne piše frontend kod.
- **Guardrail:** svaki endpoint koji menja `self_assessments` posle Approved Lock-a mora vratiti 409, testirano.
- **Model:** **Sonnet 5** za rutinske endpoint-e/servise po već postavljenom obrascu (Sekcija 8.9 — konzistentnost sloja). **Opus 5** kad se dotiče Approved Lock logika, konsenzus engine ili bilo šta što presijeca sa RLS-om.

### 7.4 Frontend Agent (Next.js / React)

- **Mandat:** Next.js 15 App Router, role-based UI (Employee/CAETeamMember/CAFLead/Sponsor/EFA), Vođeni Čarobnjak, dashboard-i (radar spidogram, 2x2 matrica), potpuna dvojezičnost i teme (vidi Sekciju 6 — i18n nije opciono, testira se u oba jezika).
- **Radi:** Faza 1 (Guided Wizard, SAR unos), Faza 2 (Government View dashboard), Faza 3 (EFA portal UI).
- **Ne radi:** ne definiše API kontrakte (konzumira ono što Backend/Arhitekta definišu), ne odlučuje o šemi baze.
- **Alat/skill:** `design:ux-copy`, `design:accessibility-review` za WCAG provere prije nego što se bilo šta proglasi "AAA pristupačno".
- **Model:** **Sonnet 5.** Komponente i stranice grade se po već definisanom dizajn sistemu i API kontraktu — ovo je najbolji balans brzina/cijena/kvalitet za obiman, obrazac-vođen rad.

### 7.5 AI/Consensus Engine Agent

- **Mandat:** hibridni LLM sloj za predlog ocjena i sažimanje teksta, uz **obavezan** Offline Math Fallback (aritmetička sredina PDCA ocjena + spajanje teksta) kad AI provajder nije dostupan.
- **Radi:** isključivo unutar Faze 1 servisnog sloja, u koordinaciji sa Backend agentom. Bira konkretan, stvarno postojeći LLM model/provajder (ne izmišljene nazive) i to upisuje u Sekciju 2 ovog fajla. Jezik sesije je obavezan parametar svakog poziva (vidi Sekciju 6.2) — generisanje pa prevod nije dozvoljen pristup.
- **Guardrail:** svaki AI predlog ocjene mora imati human-in-the-loop potvrdu prije upisa; fallback mora biti testiran nezavisno od dostupnosti interneta.
- **Model:** **Opus 5.** Dizajn dualnog konsenzus mehanizma (AI + fallback, oba moraju dati konzistentan rezultat) je suptilna logika gdje su edge-case-ovi (AI nedostupan usred poziva, djelimičan odgovor) lako previdivi na jeftinijem modelu.

### 7.6 Vault & Documents Agent (MinIO)

- **Mandat:** MinIO integracija, SHA-256 potpis dokumenata, ClamAV sken, upravljanje prilozima/dokazima uz SAR.
- **Radi:** Faza 1 (upload/verifikacija dokaza).
- **Guardrail:** nijedan fajl se ne smatra "sačuvanim dokazom" dok ne prođe i potpis i AV sken; neuspešan sken = fajl odbijen, ne tiho zanemaren.
- **Model:** **Sonnet 5.** Integracija sa poznatim, dobro dokumentovanim SDK-jem (MinIO klijent) — obrazac-vođen rad, ne otvoren arhitektonski problem.

### 7.7 QA / Test Agent

- **Mandat:** test strategija i pokrivenost za svaki modul (Sekcija 3, pravilo 6) — pytest + testcontainers za RLS/Approved Lock scenarije, integracioni testovi za konsenzus engine, E2E za Guided Wizard tok.
- **Radi:** paralelno sa svakim modulom, ne posle njega — svaki modul se smatra "gotovim" tek kad QA agent potvrdi pokrivenost kritičnih puteva (RLS izolacija, Approved Lock, AI fallback).
- **Alat/skill:** `engineering:testing-strategy`, `engineering:code-review`.
- **Model:** **Opus 5** za testove koji dokazuju RLS izolaciju i Approved Lock (moraju pokriti prave edge-case-ove, ne površne happy-path testove). **Sonnet 5** za rutinsko proširenje pokrivenosti po već postavljenom test skeletonu.

### 7.8 DevOps / Deployment Agent

- **Mandat:** CI/CD, infrastruktura, monitoring/observability, backup/DR plan, produkcioni deployment.
- **Radi:** aktivira se od Faze 0 (osnovni CI za testove) do pune snage u Fazi 5 (produkcioni deploy, najkasnije februar 2027).
- **Guardrail:** ništa ne ide u produkciju bez zelenog CI-ja, prolaska sigurnosne revizije i tvog (Team Lead) odobrenja — vidi `engineering:deploy-checklist`.
- **Alat/skill:** `engineering:deploy-checklist`, `engineering:incident-response` (za posle-deploy scenarije).
- **Model:** **Sonnet 5** za standardnu CI/CD konfiguraciju (dobro poznati, standardizovani obrasci). **Opus 5** za produkcioni deploy plan, backup/DR strategiju i sigurnosnu reviziju pred Fazu 5 — ovo je jednokratna, visokorizična odluka.

### 7.9 Kako agenti sarađuju (kratko pravilo)

Redoslijed poziva unutar jednog modula: **Arhitekta** (ako je nova odluka potrebna) → **Database/Backend/Frontend/AI/Vault** (paralelno, u granicama svog mandata) → **QA** (potvrđuje pokrivenost) → **DevOps** (CI status) → **ti** (odobrenje za sledeću fazu). Nijedan agent ne preskače tvoje odobrenje za prelazak faze, čak i ako je njegov deo tehnički završen.

### 7.10 Model po agentu — sažetak (odluka Team Lead-a, 15.9.2026)

Linija modela u septembru 2026: **Fable 5.1** (najzahtjevnije rezonovanje, najskuplji) → **Opus 5** (kompleksno agentsko kodiranje, enterprise rad) → **Sonnet 5** (balans brzina/cijena/kvalitet) → **Haiku 4.5** (mehanički, niskorizični zadaci). Princip dodjele: **model prati rizik grešk e, ne prati "težinu" zadatka po osjećaju.**

| Agent | Podrazumijevani model | Kad eskalirati na Opus 5 (ako je default Sonnet) |
|---|---|---|
| Team Lead (ti) | — (ljudska odluka) | — |
| Chief Architect | **Opus 5** | uvijek — arhitektura je po definiciji visok rizik |
| Database & Security (RLS/Lock) | **Opus 5** | uvijek — najveći bezbjednosni rizik u sistemu |
| Backend (FastAPI) | **Sonnet 5** | kad se dotiče Approved Lock, konsenzus engine, RLS presjek |
| Frontend (Next.js) | **Sonnet 5** | rijetko — samo kod kompleksnih state-machine tokova (npr. Wizard sa granastim validacionim pravilima) |
| AI/Consensus Engine | **Opus 5** | uvijek — dualni fallback mehanizam je suptilan |
| Vault & Documents (MinIO) | **Sonnet 5** | rijetko — samo ako se mijenja sigurnosni model skeniranja |
| QA/Test | **Opus 5** za RLS/Lock testove; **Sonnet 5** za ostalo | — |
| DevOps/Deployment | **Sonnet 5** | pred Fazu 5 — produkcioni deploy plan i security review idu na Opus 5 |

**Haiku 4.5** se ne dodjeljuje nijednom agentu kao podrazumijevani — koristi se ad-hoc, unutar bilo kog agenta, samo za mehaničke potpodzadatke (formatiranje, prevod statičkih stringova, sitne skripte) koje sam agent po potrebi izdvoji. **Fable 5.1** se ne koristi kao default nigdje — poziva se ručno, od strane tebe, samo kad Opus 5 vidljivo "zapne" na posebno teškom arhitektonskom problemu (npr. dizajn agregacije za Nivo 2 u Fazi 2).

Ova tabela je odluka Team Lead-a i mijenja se samo tvojim eksplicitnim nalogom, zapisanim ovdje sa datumom — isto pravilo kao za fazni plan (Sekcija 4).

---

## 9. Rečnik pojmova (za konzistentnost u kodu i komunikaciji)

- **SAR** — Self-Assessment Report (samoprocjena)
- **SAG** — Self-Assessment Group (tim koji sprovodi samoprocjenu u instituciji)
- **CAFLead** — vodi CAF proces u instituciji
- **Approved Lock** — trajno zaključavanje odobrenog SAR-a na nivou baze (SQL trigger, ne samo aplikaciona logika)
- **EFA** — External Feedback Actor (eksterni ocjenjivač za CER)
- **CER** — CAF Excellence Recognition (CER*, CER**, CER***)
- **NO** — Nacionalni organizator (koordinira CER proces na državnom nivou)
- **CIP** — Continuous Improvement Plan / akcioni plan poboljšanja
