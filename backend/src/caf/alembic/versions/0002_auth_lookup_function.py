"""Login lookup mimo RLS-a — SECURITY DEFINER funkcija auth_lookup_user().

Problem: RLS na `users` zahtijeva tenant kontekst, a pri loginu ga još
nema (institucija se saznaje TEK iz pronađenog korisnika). Rješenje NIJE
admin konekcija iz aplikacije (probila bi cijeli model), nego jedna
uska, revizibilna funkcija koja vraća samo kolone potrebne za
autentifikaciju, isključivo po tačnom email-u. app_user dobija samo
EXECUTE — i dalje nema SELECT nad tuđim redovima.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-15
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth_lookup_user(p_email text)
        RETURNS TABLE (
            id uuid,
            institution_id uuid,
            hashed_password text,
            role user_role,
            lang text
        )
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        SET search_path = public, pg_temp
        AS $$
            SELECT u.id, u.institution_id, u.hashed_password, u.role, u.lang
            FROM users u
            WHERE lower(u.email) = lower(p_email)
            LIMIT 1;
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION auth_lookup_user(text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_user(text) TO app_user")

    # Isti razlog, druga strana: poslije USPJEŠNOG logina servis smije
    # ažurirati samo (a) heš lozinke (tiha nadogradnja Argon2 parametara)
    # i (b) izabrani jezik — i to samo za korisnika koji se upravo
    # autentifikovao. Tenant konteksta još nema, pa opet SECURITY DEFINER,
    # ograničen na tačno te dvije kolone.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth_update_user_login(
            p_user_id uuid, p_hashed_password text, p_lang text
        )
        RETURNS void
        LANGUAGE sql
        SECURITY DEFINER
        SET search_path = public, pg_temp
        AS $$
            UPDATE users
            SET hashed_password = COALESCE(p_hashed_password, hashed_password),
                lang = COALESCE(p_lang, lang),
                updated_at = now()
            WHERE id = p_user_id;
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION auth_update_user_login(uuid, text, text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION auth_update_user_login(uuid, text, text) TO app_user")
    # Email je case-insensitive identitet — unikatnost mora važiti i za
    # "Ana@x.me" vs "ana@x.me", inače lookup po lower() postaje dvosmislen.
    op.execute("CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email))")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_email_lower")
    op.execute("DROP FUNCTION IF EXISTS auth_update_user_login(uuid, text, text)")
    op.execute("DROP FUNCTION IF EXISTS auth_lookup_user(text)")
