"""
Declarative base za SQLAlchemy 2.0 ORM modele.

Database & Security Agent (CLAUDE.md Sekcija 7.2). Svi modeli u
`caf/models/` nasleđuju `Base` odavde — jedan zajednički metadata
objekat, potreban Alembic-u za autogenerate migracije.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Zajednički predak svih ORM modela u aplikaciji."""

    pass


class TimestampMixin:
    """
    Mixin za `created_at` / `updated_at` kolone.

    Dvostruki default (namjerno):
    - `default` (Python strana, UTC, timezone-aware) — ORM upisi dobijaju
      identičnu vrijednost nezavisno od timezone-a DB servera.
    - `server_default=now()` — upisi koji zaobilaze ORM (raw SQL u
      testovima, ručni admin upiti, seed skripte) i dalje dobijaju
      vrijednost umjesto NOT NULL greške. Migracija 0001 definiše isti
      server_default.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
