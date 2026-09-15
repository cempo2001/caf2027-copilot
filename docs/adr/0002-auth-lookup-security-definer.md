# ADR-0002: Login bez tenant konteksta — SECURITY DEFINER lookup

- **Status:** Prihvaćeno (Faza 0, 15.9.2026)
- **Vlasnik:** Database & Security Agent (7.2); implementacija Backend Agent (7.3)

## Kontekst

RLS na `users` (ADR-0001) zahtijeva `app.current_institution_id`, ali pri loginu institucija se saznaje TEK iz pronađenog korisnika. Direktan `SELECT` kao `app_user` vraća prazan skup.

## Odbačene opcije

- **Admin konekcija iz aplikacije za login** — jedna privilegovana konekcija u runtime-u probija cijeli model (i pool je dijeljen).
- **RLS politika "dozvoli SELECT po email-u"** — nemoguće izraziti bez konteksta; svaka varijanta otkriva postojanje tuđih naloga.

## Odluka

Dvije uske `SECURITY DEFINER` funkcije (migracija 0002), `search_path` fiksiran, `REVOKE ALL FROM PUBLIC`, `GRANT EXECUTE` samo `app_user`:

- `auth_lookup_user(email)` → `(id, institution_id, hashed_password, role, lang)` po tačnom, case-insensitive email-u. Ništa više.
- `auth_update_user_login(id, hash|NULL, lang|NULL)` → poslije **uspješne** verifikacije: tiha nadogradnja Argon2 heša i pamćenje izabranog jezika. Samo te dvije kolone.

Unikatnost email-a je case-insensitive (`uq_users_email_lower`).

Aplikativni sloj: Argon2id (`argon2-cffi`), constant-time putanja za nepostojeći email (isti odgovor i vrijeme kao pogrešna lozinka).

## Preduslov (VAŽNO za deploy)

Vlasnik funkcija = rola koja pokreće migracije (`ADMIN_DATABASE_URL`). Pošto su tabele pod `FORCE ROW LEVEL SECURITY`, ta rola mora biti superuser ili imati `BYPASSRLS` — inače bi funkcija, iako DEFINER, vidjela prazan `users`. U Docker/produkcijskom Postgres-u `POSTGRES_USER` je superuser; u managed okruženjima (Faza 5) ovo se eksplicitno provjerava u deploy checklisti.
