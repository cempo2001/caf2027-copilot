"""
Aplikaciona konfiguracija — CAF 2027 Copilot backend.

CLAUDE.md Sekcija 3, pravilo 4 (Security by Design): sve tajne dolaze
isključivo preko environment promenljivih (.env u developmentu, pravi
secret store u produkciji). Nikad hardkodovane vrednosti u kodu.

Database & Security Agent (CLAUDE.md Sekcija 8.2) je vlasnik ovog fajla.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
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
