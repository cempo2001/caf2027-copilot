"""
FastAPI dependencies — spaja auth (JWT), DB sesiju, RLS tenant kontekst i
jezik. JEDINO mjesto gdje se ti slojevi spajaju. Routeri dobijaju već
sastavljen servis i ne postavljaju RLS kontekst sami.
"""

from typing import Annotated, cast

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.config import Settings, get_settings
from caf.core.i18n import Locale
from caf.core.security import TokenPayload, decode_access_token
from caf.db.rls import bind_tenant_context
from caf.db.session import get_db_session
from caf.services.auth_service import AuthService
from caf.services.institution_service import InstitutionService
from caf.services.sar_service import SarService

_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenPayload:
    """Dekoduje i validira JWT. Ne dira bazu. InvalidTokenError -> 401 (main.py)."""
    return decode_access_token(settings=settings, token=credentials.credentials)


def get_language(user: Annotated[TokenPayload, Depends(get_current_user)]) -> Locale:
    """
    CLAUDE.md 6.2: jezik ulogovanog korisnika je JWT claim (eksplicitan
    izbor pri loginu), ne Accept-Language header.
    """
    return cast(Locale, user.lang)


async def get_tenant_db_session(
    user: Annotated[TokenPayload, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AsyncSession:
    """
    Standardna sesija za SVE Nivo-1 rute. `bind_tenant_context` vezuje
    RLS kontekst za sesiju tako da važi u SVAKOJ transakciji request-a
    (i poslije commit-a) — servisi nikad ne postavljaju kontekst sami.
    """
    bind_tenant_context(session, user.institution_id)
    return session


# --- Servisi kao dependency-ji (router ostaje tanak) -------------------


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    """Login NEMA tenant kontekst (još ne zna instituciju) — obična sesija."""
    return AuthService(session, settings)


def get_sar_service(
    session: Annotated[AsyncSession, Depends(get_tenant_db_session)],
    user: Annotated[TokenPayload, Depends(get_current_user)],
    locale: Annotated[Locale, Depends(get_language)],
) -> SarService:
    return SarService(session, user, locale)


def get_institution_service(
    session: Annotated[AsyncSession, Depends(get_tenant_db_session)],
    user: Annotated[TokenPayload, Depends(get_current_user)],
    locale: Annotated[Locale, Depends(get_language)],
) -> InstitutionService:
    return InstitutionService(session, user, locale)
