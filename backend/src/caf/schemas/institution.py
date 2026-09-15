"""Institution DTO — api-contract-v1.md, sekcija 3."""

from typing import Literal
from uuid import UUID

from caf.schemas.common import OrmModel


class InstitutionOut(OrmModel):
    id: UUID
    name_me: str
    name_en: str
    sag_members_count: int
    # "caf_user" status se dodjeljuje u Fazi 2 (Nivo 2) — do tada null/in_progress.
    maturity_status: Literal["in_progress", "caf_user"] | None = None
