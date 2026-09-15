"""Faza 0 — inicijalna šema: institutions, users, subcriteria, self_assessments,
subcriteria_scores. RLS politike i Approved Lock trigger.

Database & Security Agent (CLAUDE.md Sekcija 7.2). RUČNO pisana migracija
(ne autogenerate) — RLS politike, trigger funkcije i kompozitne
garancije Alembic autogenerate ne prepoznaje.

Revision ID: 0001
Revises:
Create Date: 2026-09-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# create_type=False: tipove kreiramo JEDNOM, eksplicitno (niže). Bez ovoga
# SQLAlchemy pokušava CREATE TYPE ponovo pri svakom create_table koji
# koristi tip -> "type already exists" (greška uhvaćena u prvom test run-u).
USER_ROLE = postgresql.ENUM(
    "sponsor",
    "caf_lead",
    "cae_team_member",
    "employee",
    "national_organizer",
    "efa_evaluator",
    name="user_role",
    create_type=False,
)
SAR_STATUS = postgresql.ENUM("draft", "submitted", "approved", name="sar_status", create_type=False)

TENANT_TABLES = ("institutions", "users", "self_assessments", "subcriteria_scores")
ALL_TABLES = ("institutions", "users", "subcriteria", "self_assessments", "subcriteria_scores")

# NULLIF je obavezan: kad se custom GUC jednom postavi u sesiji (čak i sa
# is_local=true), POSLIJE transakcije vraća '' umjesto NULL. Na pooled
# konekciji bi ''::uuid bacio "invalid input syntax for type uuid"
# umjesto da vrati prazan rezultat. Sa NULLIF: nema konteksta -> NULL ->
# nijedan red ne prolazi (fail-closed).
CURRENT_INSTITUTION = "NULLIF(current_setting('app.current_institution_id', true), '')::uuid"


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Enum tipovi
    # ------------------------------------------------------------------
    postgresql.ENUM(*USER_ROLE.enums, name="user_role").create(bind, checkfirst=True)
    postgresql.ENUM(*SAR_STATUS.enums, name="sar_status").create(bind, checkfirst=True)

    # ------------------------------------------------------------------
    # 2. Tabele
    # ------------------------------------------------------------------
    op.create_table(
        "institutions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name_me", sa.String(255), nullable=False),
        sa.Column("name_en", sa.String(255), nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", USER_ROLE, nullable=False),
        sa.Column("lang", sa.String(2), nullable=False, server_default="me"),
        *_timestamps(),
    )
    op.create_index("ix_users_institution_id", "users", ["institution_id"])

    op.create_table(
        "subcriteria",
        sa.Column("code", sa.String(4), primary_key=True),
        sa.Column("criterion_number", sa.Integer, nullable=False),
        sa.Column("name_me", sa.String(500), nullable=True),
        sa.Column("name_en", sa.String(500), nullable=True),
        sa.Column("guiding_question_me", sa.Text, nullable=True),
        sa.Column("guiding_question_en", sa.Text, nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False),
    )

    op.create_table(
        "self_assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", SAR_STATUS, nullable=False, server_default="draft"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        *_timestamps(),
        # Meta za kompozitni FK iz subcriteria_scores.
        sa.UniqueConstraint("id", "institution_id", name="uq_self_assessments_id_institution"),
    )
    op.create_index("ix_self_assessments_institution_id", "self_assessments", ["institution_id"])

    op.create_table(
        "subcriteria_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("self_assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Denormalizovano radi prostih RLS politika — konzistentnost sa
        # roditeljskim SAR-om garantuje kompozitni FK niže.
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "subcriteria_code",
            sa.String(4),
            sa.ForeignKey("subcriteria.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer, nullable=True),
        sa.Column("evidence_text", sa.Text, nullable=True),
        sa.Column("weaknesses_text", sa.Text, nullable=True),
        sa.Column("input_lang", sa.String(2), nullable=False, server_default="me"),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["self_assessment_id", "institution_id"],
            ["self_assessments.id", "self_assessments.institution_id"],
            ondelete="CASCADE",
            name="fk_subcriteria_scores_sar_institution",
        ),
        sa.CheckConstraint("score IS NULL OR (score >= 1 AND score <= 5)", name="ck_score_range"),
        sa.CheckConstraint("input_lang IN ('me', 'en')", name="ck_input_lang_valid"),
        sa.UniqueConstraint("self_assessment_id", "subcriteria_code", name="uq_sar_subcriteria_once"),
    )
    op.create_index(
        "ix_subcriteria_scores_institution_id", "subcriteria_scores", ["institution_id"]
    )
    op.create_index(
        "ix_subcriteria_scores_self_assessment_id", "subcriteria_scores", ["self_assessment_id"]
    )

    # ------------------------------------------------------------------
    # 3. GRANT — app_user (bez BYPASSRLS, infra/postgres/init-rls.sh)
    #    mora imati table-level privilegije; RLS ograničava REDOVE, ne
    #    pristup tabeli. `subcriteria` je referentna tabela: app_user je
    #    samo čita — izmjena zvaničnog CAF okvira nije aplikativna radnja.
    # ------------------------------------------------------------------
    for table in TENANT_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_user")
    op.execute("GRANT SELECT ON subcriteria TO app_user")

    # ------------------------------------------------------------------
    # 4. Row Level Security (fail-closed)
    #    FORCE: RLS važi i za vlasnika tabele ako nije superuser —
    #    buduća promjena vlasništva ne može tiho probiti izolaciju.
    #    Politika bez WITH CHECK -> Postgres koristi USING i za
    #    INSERT/UPDATE provjeru (ne može se upisati red tuđe institucije).
    # ------------------------------------------------------------------
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    op.execute(
        f"CREATE POLICY institutions_tenant_isolation ON institutions "
        f"USING (id = {CURRENT_INSTITUTION})"
    )
    for table in ("users", "self_assessments", "subcriteria_scores"):
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table} "
            f"USING (institution_id = {CURRENT_INSTITUTION})"
        )

    # ------------------------------------------------------------------
    # 5. Approved Lock — CLAUDE.md Sekcija 1 i Sekcija 3, pravilo 3.
    #
    #    SECURITY DEFINER (namjerno): status roditeljskog SAR-a se čita
    #    kao vlasnik funkcije, MIMO RLS-a. Da je trigger SECURITY INVOKER,
    #    upit na self_assessments bi prošao kroz RLS pozivaoca — a RLS
    #    koji iz bilo kog razloga ne vidi SAR značio bi "nije approved"
    #    i tihi PROBOJ lock-a. Lock mora biti nezavisan od tenant konteksta.
    #    search_path je fiksiran (standardna zaštita SECURITY DEFINER
    #    funkcija od search_path hijacking-a).
    #
    #    ERRCODE P0001 + poruka 'sar_locked' — servisni sloj (Korak 5) ovo
    #    mapira na caf.core.exceptions.SarLockedError (HTTP 409).
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION check_approved_sar_lock()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public, pg_temp
        AS $$
        DECLARE
            parent_status sar_status;
        BEGIN
            IF TG_TABLE_NAME = 'self_assessments' THEN
                -- Odobren SAR je nepromjenljiv i neobrisiv. Prelaz KA
                -- 'approved' je dozvoljen (OLD.status tada nije approved).
                IF OLD.status = 'approved' THEN
                    RAISE EXCEPTION 'sar_locked' USING ERRCODE = 'P0001';
                END IF;
                IF TG_OP = 'DELETE' THEN
                    RETURN OLD;
                END IF;
                RETURN NEW;
            END IF;

            IF TG_TABLE_NAME = 'subcriteria_scores' THEN
                -- Provjera i starog i novog roditelja: UPDATE ne smije
                -- "premjestiti" red IZ odobrenog SAR-a, niti U odobreni.
                IF TG_OP IN ('UPDATE', 'DELETE') THEN
                    SELECT status INTO parent_status
                    FROM self_assessments WHERE id = OLD.self_assessment_id;
                    IF parent_status = 'approved' THEN
                        RAISE EXCEPTION 'sar_locked' USING ERRCODE = 'P0001';
                    END IF;
                END IF;
                IF TG_OP IN ('INSERT', 'UPDATE') THEN
                    SELECT status INTO parent_status
                    FROM self_assessments WHERE id = NEW.self_assessment_id;
                    IF parent_status = 'approved' THEN
                        RAISE EXCEPTION 'sar_locked' USING ERRCODE = 'P0001';
                    END IF;
                END IF;
                IF TG_OP = 'DELETE' THEN
                    RETURN OLD;
                END IF;
                RETURN NEW;
            END IF;

            RAISE EXCEPTION 'check_approved_sar_lock: neočekivana tabela %', TG_TABLE_NAME;
        END;
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION check_approved_sar_lock() FROM PUBLIC")

    op.execute(
        "CREATE TRIGGER trg_self_assessments_approved_lock "
        "BEFORE UPDATE OR DELETE ON self_assessments "
        "FOR EACH ROW EXECUTE FUNCTION check_approved_sar_lock()"
    )
    op.execute(
        "CREATE TRIGGER trg_subcriteria_scores_approved_lock "
        "BEFORE INSERT OR UPDATE OR DELETE ON subcriteria_scores "
        "FOR EACH ROW EXECUTE FUNCTION check_approved_sar_lock()"
    )

    # ------------------------------------------------------------------
    # 6. Seed — SAMO struktura CAF okvira (9 kriterijuma / 28
    #    podkriterijuma; distribucija 4-4-3-6-3 za Enablere 1-5 i
    #    2-2-2-2 za Rezultate 6-9). Nazivi i usmjeravajuća pitanja ostaju
    #    NULL dok se ne unesu iz zvaničnog EIPA teksta — vidi
    #    caf.models.subcriteria. Distribuciju takođe potvrditi prema
    #    zvaničnom dokumentu prije Faze 1 UI-ja.
    # ------------------------------------------------------------------
    distribution = {1: 4, 2: 4, 3: 3, 4: 6, 5: 3, 6: 2, 7: 2, 8: 2, 9: 2}
    rows = []
    order = 0
    for criterion, count in distribution.items():
        for sub in range(1, count + 1):
            order += 1
            rows.append(
                {"code": f"{criterion}.{sub}", "criterion_number": criterion, "display_order": order}
            )
    assert len(rows) == 28, f"CAF okvir mora imati 28 podkriterijuma, seed ima {len(rows)}"

    subcriteria_table = sa.table(
        "subcriteria",
        sa.column("code", sa.String),
        sa.column("criterion_number", sa.Integer),
        sa.column("display_order", sa.Integer),
    )
    op.bulk_insert(subcriteria_table, rows)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_subcriteria_scores_approved_lock ON subcriteria_scores")
    op.execute("DROP TRIGGER IF EXISTS trg_self_assessments_approved_lock ON self_assessments")
    op.execute("DROP FUNCTION IF EXISTS check_approved_sar_lock()")

    op.drop_table("subcriteria_scores")
    op.drop_table("self_assessments")
    op.drop_table("subcriteria")
    op.drop_table("users")
    op.drop_table("institutions")

    op.execute("DROP TYPE IF EXISTS sar_status")
    op.execute("DROP TYPE IF EXISTS user_role")
