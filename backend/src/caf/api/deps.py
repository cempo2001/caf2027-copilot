"""
FastAPI dependencies — spaja auth (JWT), DB sesiju, RLS tenant kontekst i
jezik. JEDINO mjesto gdje se ti slojevi spajaju. Routeri dobijaju već
sastavljen servis i ne postavljaju RLS kontekst sami.
"""

from functools import lru_cache
from typing import Annotated, cast

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from caf.core.config import Settings, get_settings
from caf.core.i18n import Locale
from caf.core.security import TokenPayload, decode_access_token
from caf.db.rls import bind_tenant_context
from caf.db.session import get_db_session
from caf.integrations.ai_provider import ScoreSuggestionProvider, build_ai_provider
from caf.integrations.clamav import AvScanner, ClamdScanner
from caf.integrations.object_storage import MinioObjectStorage, ObjectStorage
from caf.services.auth_service import AuthService
from caf.services.cip_service import CipService
from caf.services.consensus_service import ConsensusService
from caf.services.evidence_service import EvidenceService
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


def get_cip_service(
    session: Annotated[AsyncSession, Depends(get_tenant_db_session)],
    user: Annotated[TokenPayload, Depends(get_current_user)],
    locale: Annotated[Locale, Depends(get_language)],
) -> CipService:
    return CipService(session, user, locale)


# --- Spoljni servisi (trezor, antivirus, AI) — testovi ih zamjenjuju -----


@lru_cache
def _minio_storage(
    endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool
) -> MinioObjectStorage:
    # Jedan klijent (i connection pool) po konfiguraciji, ne po zahtjevu.
    return MinioObjectStorage(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        secure=secure,
    )


def get_object_storage(settings: Annotated[Settings, Depends(get_settings)]) -> ObjectStorage:
    return _minio_storage(
        settings.minio_endpoint,
        settings.minio_root_user,
        settings.minio_root_password,
        settings.minio_bucket_evidence,
        settings.minio_secure,
    )


def get_av_scanner(settings: Annotated[Settings, Depends(get_settings)]) -> AvScanner | None:
    """None SAMO za AV_SCAN_MODE=disabled (lokalni razvoj; produkcija to odbija)."""
    if settings.av_scan_mode == "disabled":
        return None
    return ClamdScanner(
        settings.clamav_host, settings.clamav_port, settings.clamav_timeout_seconds
    )


def get_ai_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ScoreSuggestionProvider | None:
    return build_ai_provider(settings)


def get_evidence_service(
    session: Annotated[AsyncSession, Depends(get_tenant_db_session)],
    user: Annotated[TokenPayload, Depends(get_current_user)],
    locale: Annotated[Locale, Depends(get_language)],
    settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    scanner: Annotated[AvScanner | None, Depends(get_av_scanner)],
) -> EvidenceService:
    return EvidenceService(
        session,
        user,
        locale,
        storage=storage,
        scanner=scanner,
        max_bytes=settings.max_evidence_bytes,
    )


def get_consensus_service(
    session: Annotated[AsyncSession, Depends(get_tenant_db_session)],
    user: Annotated[TokenPayload, Depends(get_current_user)],
    locale: Annotated[Locale, Depends(get_language)],
    provider: Annotated[ScoreSuggestionProvider | None, Depends(get_ai_provider)],
) -> ConsensusService:
    return ConsensusService(session, user, locale, provider=provider)
