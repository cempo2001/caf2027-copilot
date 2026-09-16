"""
Aplikaciona konfiguracija — CAF 2027 Copilot backend.

CLAUDE.md Sekcija 3, pravilo 4 (Security by Design): sve tajne dolaze
isključivo preko environment promenljivih (.env u developmentu, pravi
secret store u produkciji). Nikad hardkodovane vrednosti u kodu.

Database & Security Agent (CLAUDE.md Sekcija 8.2) je vlasnik ovog fajla.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralna konfiguracija, učitana jednom pri startu aplikacije.

    Validacija (Pydantic v2) osigurava da aplikacija odbija da se pokrene
    sa nekompletnom ili pogrešno tipizovanom konfiguracijom, umjesto da
    padne kasnije, u produkciji, na prvom stvarnom pozivu.
    """

    model_config = SettingsConfigDict(
        # Podržava pokretanje i iz repo root-a (docker, gdje env vars dolaze
        # kroz docker-compose `environment:`) i iz `backend/` foldera
        # (lokalni `pytest`/`uvicorn`, gdje se .env čita direktno sa diska).
        # Kasniji fajl u tuple-u prepisuje ranije — oba se provjeravaju,
        # ne pada ako jedan ne postoji.
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Okruženje ---
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # --- Baza podataka ---
    database_url: PostgresDsn = Field(
        ...,
        description="RUNTIME konekcija — app_user rola (bez BYPASSRLS, bez DDL prava).",
    )
    # Migracije (Alembic) zahtijevaju DDL prava koje app_user NAMJERNO
    # nema. Odvojena konekcija kao vlasnik baze (POSTGRES_USER). Nikad se
    # ne koristi iz FastAPI runtime-a — samo iz alembic/env.py.
    admin_database_url: PostgresDsn | None = Field(
        default=None,
        description="Konekcija za Alembic migracije — POSTGRES_USER (vlasnik baze).",
    )

    # --- Redis ---
    redis_url: RedisDsn = Field(...)

    # --- MinIO / Dokazni trezor ---
    minio_endpoint: str = Field(...)
    minio_root_user: str = Field(...)
    minio_root_password: str = Field(...)
    minio_bucket_evidence: str = Field(default="caf-evidence")
    # Lokalni docker-compose MinIO radi bez TLS-a; produkcija mora imati TLS.
    minio_secure: bool = Field(default=False)

    # --- Antivirus (ClamAV, clamd INSTREAM) — CLAUDE.md 7.6 ---
    # "clamd": svaki fajl se skenira; skener nedostupan -> 503, fajl se NE čuva.
    # "disabled": SAMO lokalni razvoj bez ClamAV-a — fajl se čuva kao
    # `pending` (nije verifikovan dokaz). Zabranjeno u produkciji (validator).
    av_scan_mode: Literal["clamd", "disabled"] = "clamd"
    clamav_host: str = Field(default="localhost")
    clamav_port: int = Field(default=3310, ge=1, le=65535)
    clamav_timeout_seconds: float = Field(default=60.0, gt=0)

    # --- Dokazi (api-contract-v1.md 6.1) ---
    max_evidence_bytes: int = Field(default=25 * 1024 * 1024, gt=0)

    # --- JWT / Auth ---
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)

    # --- AI Provider ---
    # Ostaje prazno dok AI/Consensus Engine agent ne izabere stvaran,
    # verifikovan model (CLAUDE.md Sekcija 2, napomena o AI modelima).
    # Servis mora raditi ispravno i kad su ova polja prazna — tada se
    # koristi isključivo Offline Math Fallback.
    ai_provider: str = Field(default="")
    ai_api_key: str = Field(default="")
    ai_model: str = Field(default="")

    # --- i18n (CLAUDE.md Sekcija 6) ---
    default_locale: Literal["me", "en"] = "me"
    supported_locales: str = Field(default="me,en")

    @model_validator(mode="after")
    def _forbid_unscanned_evidence_in_production(self) -> "Settings":
        if self.environment == "production" and self.av_scan_mode != "clamd":
            raise ValueError("AV_SCAN_MODE mora biti 'clamd' u produkciji (CLAUDE.md 7.6).")
        if self.environment == "production" and not self.minio_secure:
            raise ValueError("MINIO_SECURE mora biti true u produkciji (TLS do dokaznog trezora).")
        return self

    @property
    def supported_locales_list(self) -> list[str]:
        return [loc.strip() for loc in self.supported_locales.split(",") if loc.strip()]

    @property
    def migration_database_url(self) -> str:
        return str(self.admin_database_url or self.database_url)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Cached factory — Settings se instancira jednom po procesu.
    Koristiti kao FastAPI dependency (`Depends(get_settings)`), ne
    globalni import objekta, radi lakšeg testiranja (override u testovima).
    """
    return Settings()
