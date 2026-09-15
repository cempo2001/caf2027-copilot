"""
User — pripadnik SAG tima jedne institucije (CLAUDE.md Sekcija 1).

Uloga (`role`) je isti skup vrijednosti kao `caf.core.security.Role` —
vidi napomenu uz `RoleEnum` o tome zašto su ovo dvije odvojene
definicije koje moraju ostati sinhronizovane.
"""

import uuid
from enum import StrEnum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from caf.db.base import Base, TimestampMixin


class RoleEnum(StrEnum):
    """
    NAMJERNO odvojeno od `caf.core.security.Role` (isti stringovi, ista
    lista). `security.Role` je čist Python enum za JWT claim validaciju
    bez ikakve zavisnosti od ORM sloja (Sekcija 3, pravilo 2). Nova
    uloga se dodaje NA OBA MJESTA i u migraciju (ALTER TYPE user_role).
    """

    SPONSOR = "sponsor"
    CAF_LEAD = "caf_lead"
    CAE_TEAM_MEMBER = "cae_team_member"
    EMPLOYEE = "employee"
    NATIONAL_ORGANIZER = "national_organizer"
    EFA_EVALUATOR = "efa_evaluator"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # values_callable: SQLAlchemy po defaultu upisuje IME enum člana
    # ("SPONSOR"), a DB tip `user_role` sadrži VRIJEDNOSTI ("sponsor").
    # create_type=False: tip kreira isključivo migracija 0001.
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(
            RoleEnum,
            name="user_role",
            native_enum=True,
            create_type=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    # Jezik izabran pri loginu — CLAUDE.md Sekcija 6.2, postaje JWT claim.
    lang: Mapped[str] = mapped_column(
        String(2), nullable=False, default="me", server_default="me"
    )

    institution: Mapped["Institution"] = relationship(back_populates="users")  # noqa: F821
