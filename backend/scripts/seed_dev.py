"""
Dev seed — test institucija + po jedan korisnik za svaku Nivo-1 ulogu.

SAMO za lokalni razvoj. Odbija rad ako je ENVIRONMENT=production
(CLAUDE.md 3.4 — nema "test" naloga u produkciji). Idempotentna:
ponovno pokretanje ne pravi duplikate.

Pokretanje (iz backend/, sa aktivnim .venv i bazom iz docker-compose):
    python scripts/seed_dev.py

Koristi ADMIN_DATABASE_URL (vlasnik baze) jer upisuje u više tabela bez
tenant konteksta — isti razlog kao migracije, vidi ADR-0001.
"""

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from caf.core.config import get_settings
from caf.core.passwords import hash_password

INSTITUTION = ("Ministarstvo zdravlja (TEST)", "Ministry of Health (TEST)")
PASSWORD = "Caf2027!"
USERS = [
    ("sponsor@test.caf", "sponsor", "me"),
    ("lead@test.caf", "caf_lead", "me"),
    ("member@test.caf", "cae_team_member", "me"),
    ("employee@test.caf", "employee", "en"),
]


async def main() -> int:
    settings = get_settings()
    if settings.is_production:
        print("ODBIJENO: seed_dev.py se ne pokreće u produkciji.", file=sys.stderr)
        return 1

    engine = create_async_engine(settings.migration_database_url)
    async with engine.begin() as conn:
        institution_id = await conn.scalar(
            text("SELECT id FROM institutions WHERE name_en = :en"), {"en": INSTITUTION[1]}
        )
        if institution_id is None:
            institution_id = await conn.scalar(
                text(
                    "INSERT INTO institutions (name_me, name_en) VALUES (:me, :en) RETURNING id"
                ),
                {"me": INSTITUTION[0], "en": INSTITUTION[1]},
            )
            print(f"+ institucija {INSTITUTION[0]} ({institution_id})")
        else:
            print(f"= institucija već postoji ({institution_id})")

        hashed = hash_password(PASSWORD)
        for email, role, lang in USERS:
            exists = await conn.scalar(
                text("SELECT 1 FROM users WHERE lower(email) = lower(:email)"), {"email": email}
            )
            if exists:
                print(f"= {email} ({role}) već postoji")
                continue
            await conn.execute(
                text(
                    "INSERT INTO users (institution_id, email, hashed_password, role, lang) "
                    "VALUES (:iid, :email, :hash, CAST(:role AS user_role), :lang)"
                ),
                {
                    "iid": str(institution_id),
                    "email": email,
                    "hash": hashed,
                    "role": role,
                    "lang": lang,
                },
            )
            print(f"+ {email} ({role})")
    await engine.dispose()

    print(f"\nLozinka za sve test naloge: {PASSWORD}")
    print("Login: POST /api/v1/auth/login  {email, password, lang: 'me'|'en'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
