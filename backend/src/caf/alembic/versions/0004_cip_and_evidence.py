"""Faza 1 — CIP stavke (api-contract-v1.md 5) i metapodaci dokaza (6.1).

Database & Security Agent (CLAUDE.md 7.2). Obje tabele prate pravila iz
ADR-0001 za svaku novu tenant tabelu:
- denormalizovan `institution_id` + kompozitni FK na self_assessments
  (id, institution_id) — konzistentnost garantuje baza, ne servis;
- ENABLE + FORCE ROW LEVEL SECURITY, politika sa NULLIF (fail-closed);
- GRANT za app_user;
- Approved Lock: `check_approved_sar_lock()` se proširuje na obje tabele
  (INSERT/UPDATE/DELETE djeteta odobrenog SAR-a -> 'sar_locked' -> 409).

`evidence_files` čuva samo METAPODATKE — sam fajl je u MinIO. Red postoji
samo za fajl koji je prošao SHA-256 i AV korak (`clean`), ili u lokalnom
razvoju sa isključenim skenerom (`pending`, nije verifikovan dokaz).
`infected` se nikad ne upisuje (CLAUDE.md 7.6).

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-16
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

CIP_QUADRANT = postgresql.ENUM(
    "quick_win", "strategic", "fill_in", "reconsider", name="cip_quadrant", create_type=False
)
CIP_STATUS = postgresql.ENUM("planned", "in_progress", "done", name="cip_status", create_type=False)

NEW_TENANT_TABLES = ("cip_items", "evidence_files")
CURRENT_INSTITUTION = "NULLIF(current_setting('app.current_institution_id', true), '')::uuid"

# Tabele-djeca SAR-a koje Approved Lock štiti. Sve imaju kolonu
# `self_assessment_id`, pa ista plpgsql grana radi za svaku (NEW/OLD se
# razrješavaju po imenu kolone u trenutku izvršavanja).
_LOCK_FUNCTION = """
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
        IF OLD.status = 'approved' THEN
            RAISE EXCEPTION 'sar_locked' USING ERRCODE = 'P0001';
        END IF;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;

    IF TG_TABLE_NAME IN ({child_tables}) THEN
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


def _lock_function_sql(tables: tuple[str, ...]) -> str:
    return _LOCK_FUNCTION.replace("{child_tables}", ", ".join(f"'{t}'" for t in tables))


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def _sar_child_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("self_assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(*CIP_QUADRANT.enums, name="cip_quadrant").create(bind, checkfirst=True)
    postgresql.ENUM(*CIP_STATUS.enums, name="cip_status").create(bind, checkfirst=True)

    op.create_table(
        "cip_items",
        *_sar_child_columns(),
        sa.Column("title_me", sa.String(300), nullable=False),
        sa.Column("title_en", sa.String(300), nullable=False),
        sa.Column("quadrant", CIP_QUADRANT, nullable=False),
        sa.Column("as_is", sa.Text, nullable=False),
        sa.Column("to_be", sa.Text, nullable=False),
        sa.Column("status", CIP_STATUS, nullable=False, server_default="planned"),
        # CLAUDE.md 6.1 — slobodan tekst (as_is/to_be) nosi jezik unosa.
        sa.Column("input_lang", sa.String(2), nullable=False, server_default="me"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["self_assessment_id", "institution_id"],
            ["self_assessments.id", "self_assessments.institution_id"],
            ondelete="CASCADE",
            name="fk_cip_items_sar_institution",
        ),
        sa.CheckConstraint("input_lang IN ('me', 'en')", name="ck_cip_items_input_lang"),
    )
    op.create_index("ix_cip_items_institution_id", "cip_items", ["institution_id"])
    op.create_index("ix_cip_items_self_assessment_id", "cip_items", ["self_assessment_id"])

    op.create_table(
        "evidence_files",
        *_sar_child_columns(),
        sa.Column(
            "subcriteria_code",
            sa.String(4),
            sa.ForeignKey("subcriteria.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(127), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(512), nullable=False, unique=True),
        sa.Column("av_scan_status", sa.String(16), nullable=False),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["self_assessment_id", "institution_id"],
            ["self_assessments.id", "self_assessments.institution_id"],
            ondelete="CASCADE",
            name="fk_evidence_files_sar_institution",
        ),
        # 'infected' namjerno NIJE dozvoljen — zaražen fajl se nikad ne upisuje.
        sa.CheckConstraint(
            "av_scan_status IN ('clean', 'pending')", name="ck_evidence_files_av_status"
        ),
        sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'", name="ck_evidence_files_sha256"),
        sa.CheckConstraint("size_bytes > 0", name="ck_evidence_files_size"),
    )
    op.create_index("ix_evidence_files_institution_id", "evidence_files", ["institution_id"])
    op.create_index(
        "ix_evidence_files_sar_code", "evidence_files", ["self_assessment_id", "subcriteria_code"]
    )

    for table in NEW_TENANT_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_user")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table} "
            f"USING (institution_id = {CURRENT_INSTITUTION})"
        )

    op.execute(_lock_function_sql(("subcriteria_scores", *NEW_TENANT_TABLES)))
    for table in NEW_TENANT_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_approved_lock "
            f"BEFORE INSERT OR UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION check_approved_sar_lock()"
        )


def downgrade() -> None:
    for table in NEW_TENANT_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_approved_lock ON {table}")
    op.execute(_lock_function_sql(("subcriteria_scores",)))
    op.drop_table("evidence_files")
    op.drop_table("cip_items")
    op.execute("DROP TYPE IF EXISTS cip_status")
    op.execute("DROP TYPE IF EXISTS cip_quadrant")
