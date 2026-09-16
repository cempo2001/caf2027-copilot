"""
E2E seed — NOVA test institucija (Sponsor + CAFLead) za svaki E2E prolaz.

QA Agent (CLAUDE.md 7.7). Playwright testovi (`frontend/e2e`) pozivaju ovu
skriptu prije svakog testa: svaka institucija počinje bez SAR-a, pa se tok
"kreiraj SAR -> ... -> Approved Lock" može ponavljati bez čišćenja baze.

SAMO lokalni razvoj / CI — odbija rad kad je ENVIRONMENT=production.
Na stdout ispisuje JEDAN red JSON-a: {"institution_id", "sponsor", "lead", "password"}.

    python scripts/seed_e2e.py
"""

import asyncio
import json
import secrets
import sys
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from caf.core.config import get_settings
from caf.core.passwords import hash_password


async def main() -> int:
    settings = get_settings()
    if settings.is_production:
        print("ODBIJENO: seed_e2e.py se ne pokreće u produkciji.", file=sys.stderr)
        return 1

    suffix = secrets.token_hex(4)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    password = f"E2e-{secrets.token_urlsafe(12)}"
    users = {
        "sponsor": f"e2e-sponsor-{suffix}@test.caf",
        "lead": f"e2e-lead-{suffix}@test.caf",
    }

    engine = create_async_engine(settings.migration_database_url)
    try:
        async with engine.begin() as conn:
            institution_id = await conn.scalar(
                text("INSERT INTO institutions (name_me, name_en) VALUES (:me, :en) RETURNING id"),
                {
                    "me": f"E2E institucija {stamp} ({suffix})",
                    "en": f"E2E institution {stamp} ({suffix})",
                },
            )
            hashed = hash_password(password)
            for role, email in (("sponsor", users["sponsor"]), ("caf_lead", users["lead"])):
                await conn.execute(
                    text(
                        "INSERT INTO users (institution_id, email, hashed_password, role, lang) "
                        "VALUES (:iid, :email, :hash, CAST(:role AS user_role), 'me')"
                    ),
                    {"iid": str(institution_id), "email": email, "hash": hashed, "role": role},
                )
    finally:
        await engine.dispose()

    print(json.dumps({"institution_id": str(institution_id), "password": password, **users}))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
