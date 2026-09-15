"""Auth DTO — api-contract-v1.md, sekcija 2."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from caf.core.security import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    # Eksplicitan izbor korisnika na login ekranu — CLAUDE.md Sekcija 6.2.
    lang: Literal["me", "en"]


class UserOut(BaseModel):
    id: UUID
    email: str
    role: Role
    institution_id: UUID
    lang: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut
