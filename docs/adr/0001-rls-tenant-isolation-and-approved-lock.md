# ADR-0001: RLS tenant izolacija i Approved Lock na nivou baze

- **Status:** Prihvaćeno (Faza 0, 15.9.2026)
- **Vlasnik:** Database & Security Agent (CLAUDE.md 7.2), review: Chief Architect (7.1)

## Kontekst

CLAUDE.md zahtijeva potpunu izolaciju institucija i trajno zaključavanje odobrenog SAR-a "na nivou baze". Oba mehanizma moraju raditi i kad aplikativni sloj ima bug.

## Odluke

1. **RLS, fail-closed.** Sve tenant tabele imaju `ENABLE` + `FORCE ROW LEVEL SECURITY`. Politika: `institution_id = NULLIF(current_setting('app.current_institution_id', true), '')::uuid`. Runtime rola `app_user` nema `BYPASSRLS`. Bez postavljenog konteksta upit vraća prazan skup.
   - `NULLIF` je obavezan: poslije transakcije Postgres vraća postavljeni custom GUC na `''`, a `''::uuid` bi bacio grešku na pooled konekcijama (pokriveno regresionim testom).
   - Kontekst se postavlja sa `is_local=true` (važi samo za transakciju), pa konekcija vraćena u pool ne nosi tuđi tenant.

2. **Denormalizovan `institution_id` u `subcriteria_scores` + kompozitni FK.** RLS ostaje prost kolonski uslov (bez subquery-ja po redu). Konzistentnost sa roditeljskim SAR-om garantuje FK `(self_assessment_id, institution_id) → self_assessments(id, institution_id)`, ne servisni sloj.

3. **Approved Lock kao `SECURITY DEFINER` trigger.** `check_approved_sar_lock()` blokira UPDATE/DELETE odobrenog SAR-a i INSERT/UPDATE/DELETE njegovih score-ova (`RAISE ... 'sar_locked'`, ERRCODE `P0001` → servisni sloj mapira na HTTP 409). Status roditelja se čita mimo RLS-a: da je trigger `SECURITY INVOKER`, SAR nevidljiv kroz RLS bi izgledao kao "nije odobren" i lock bi bio tiho probijen. `search_path` je fiksiran.
   - Lock važi i za superuser-a kroz običan DML. Namjerna administrativna izmjena zahtijeva eksplicitno isključivanje triggera — vidljiva, revizibilna radnja.

4. **`subcriteria` je referentna tabela bez RLS-a**, a `app_user` ima samo `SELECT`. Nazivi i usmjeravajuća pitanja ostaju prazni dok se ne unesu iz zvaničnog EIPA teksta.

## Posljedice

- Servisni sloj (Korak 5) vraća 409 **prije** nego upit stigne do triggera; trigger je zadnja linija odbrane.
- Svaka nova tenant tabela: `institution_id` + ENABLE/FORCE RLS + politika sa `NULLIF` + GRANT za `app_user` + test izolacije.
- Agregacija za Nivo 2 (Faza 2) zahtijeva posebnu, eksplicitno dizajniranu putanju (nova ADR) — ne proširivanje ovih politika ad hoc.
