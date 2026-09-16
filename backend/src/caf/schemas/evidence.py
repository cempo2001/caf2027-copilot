"""Evidence (dokazi) DTO — api-contract-v1.md, sekcija 6.1."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class EvidenceUploadOut(BaseModel):
    id: UUID
    filename: str
    sha256: str
    av_scan_status: Literal["clean", "pending"]
