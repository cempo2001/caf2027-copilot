#!/bin/bash
# =============================================================================
# CAF 2027 Copilot — RLS Bootstrap
# Database & Security Agent (CLAUDE.md Sekcija 7.2)
#
# Izvršava se JEDNOM pri prvom podizanju postgres kontejnera
# (docker-entrypoint-initdb.d podržava .sh skripte i pokreće ih kao psql
# klijenta sa env promenljivama kontejnera već dostupnim).
#
# Razlog zašto je ovo .sh a ne čist .sql: lozinka aplikativne role MORA
# doći iz APP_DB_PASSWORD (docker-compose environment, iz .env), ne smije
# biti zakucana u SQL fajlu — inače se lako desi baš greška koju smo
# uhvatili: SQL fajl ima jednu lozinku, .env drugu, i runtime konekcija
# puca. envsubst rešava to na jednom mjestu, iz jednog izvora istine.
# =============================================================================

set -euo pipefail

: "${APP_DB_PASSWORD:?APP_DB_PASSWORD mora biti postavljen (vidi .env / docker-compose.yml)}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Aplikacija se NIKAD ne konektuje kao superuser. Runtime konekcija
    -- ide preko app_user role BEZ BYPASSRLS, tako da RLS politike u
    -- Alembic migracijama ne mogu biti slučajno zaobiđene ni greškom u
    -- aplikativnom kodu.
    DO
    \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
            CREATE ROLE app_user WITH LOGIN PASSWORD '${APP_DB_PASSWORD}' NOBYPASSRLS;
        ELSE
            ALTER ROLE app_user WITH LOGIN PASSWORD '${APP_DB_PASSWORD}' NOBYPASSRLS;
        END IF;
    END
    \$\$;

    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO app_user;

    -- Ekstenzija za UUID primarne ključeve (institucije, korisnici, SAR-ovi)
    CREATE EXTENSION IF NOT EXISTS pgcrypto;

    COMMENT ON ROLE app_user IS
        'Runtime rola za FastAPI backend. NEMA BYPASSRLS — sve RLS politike se primenjuju na ovu rolu bez izuzetka. Lozinka dolazi iz APP_DB_PASSWORD (.env), postavljena pri svakom podizanju kontejnera.';
EOSQL

echo "[init-rls] app_user rola kreirana/ažurirana, lozinka sinhronizovana sa APP_DB_PASSWORD."
