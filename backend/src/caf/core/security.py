"""
JWT encode/decode sa custom claims (tenant_id, role, lang).

CLAUDE.md Sekcija 3, pravilo 4 (JWT sa custom claims) i Sekcija 6.2
(jezik je deo JWT claim-a, ne pretpostavljen default).
"""

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

import jwt
from pydantic import BaseModel

from caf.core.config import Settings


class Role(StrEnum):
    """Uloge unutar institucije — CLAUDE.md Sekcija 1, Nivo 1."""

    SPONSOR = "sponsor"
    CAF_LEAD = "caf_lead"
    CAE_TEAM_MEMBER = "cae_team_member"
    EMPLOYEE = "employee"
    # Rezervisano za kasnije faze (ne aktivno u Fazi 0/1):
    NATIONAL_ORGANIZER = "national_organizer"
    EFA_EVALUATOR = "efa_evaluator"


class TokenPayload(BaseModel):
    """Dekodovan i validiran sadržaj JWT-a — tipizovano, ne sirovi dict."""

    sub: UUID  # user_id
    institution_id: UUID
    role: Role
    lang: str  # "me" | "en" — CLAUDE.md Sekcija 6.2
    exp: datetime


class InvalidTokenError(Exception):
    """Podignuto kod nevalidnog, isteklog ili malformisanog tokena."""


def create_access_token(
    *,
    settings: Settings,
    user_id: UUID,
    institution_id: UUID,
    role: Role,
    lang: str,
) -> str:
    if lang not in settings.supported_locales_list:
        raise ValueError(f"Nepodržan jezik u token claim-u: {lang!r}")

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    claims: dict[str, Any] = {
        "sub": str(user_id),
        "institution_id": str(institution_id),
        "role": role.value,
        "lang": lang,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(*, settings: Settings, token: str) -> TokenPayload:
    try:
        raw = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Token je istekao.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError("Nevalidan token.") from exc

    try:
        return TokenPayload.model_validate(raw)
    except Exception as exc:  # Pydantic ValidationError
        raise InvalidTokenError("Token ima nevalidnu strukturu claim-ova.") from exc
