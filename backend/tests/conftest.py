"""
Pytest fixtures — testcontainers Postgres sa STVARNO primijenjenom
Alembic migracijom (0001_initial_schema), za RLS/Approved Lock testove.

QA Agent (CLAUDE.md Sekcija 7.7): testovi rade protiv pravog Postgres-a,
ne mock-a — RLS i trigger ponašanje je specifično za bazu.

Dvije konekcije, dvije uloge (namjerno):
- `admin_session`  — testcontainers superuser. Superuser po definiciji
  zaobilazi RLS, pa služi SAMO za pripremu podataka (više institucija).
- `app_user_session` — rola `app_user` bez BYPASSRLS, isti put kao
  produkcioni FastAPI backend. Sve provjere izolacije idu kroz nju.
"""

import os
import subprocess
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

try:  # testcontainers >= 4.x premješta modul u `community`
    from testcontainers.community.postgres import PostgresContainer
except ImportError:  # pragma: no cover
    from testcontainers.postgres import PostgresContainer

from caf.core.config import Settings
from caf.db.session import create_engine, create_session_factory

BACKEND_ROOT = Path(__file__).resolve().parent.parent
APP_USER_PASSWORD = "test_app_user_password"
JWT_TEST_SECRET = "t" * 40


def _settings_for(database_url: str) -> Settings:
    return Settings(
        _env_file=None,
        database_url=database_url,
        redis_url="redis://localhost:6379/0",
        minio_endpoint="localhost:9000",
        minio_root_user="test",
        minio_root_password="test",
        jwt_secret_key=JWT_TEST_SECRET,
    )


def _dsn(container: PostgresContainer, user: str, password: str) -> str:
    host = container.get_container_host_ip()
    port = container.get_exposed_port(5432)
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{container.dbname}"


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def migrated_database(postgres_container: PostgresContainer) -> PostgresContainer:
    """
    1) Kreira `app_user` (ekvivalent infra/postgres/init-rls.sh) preko
       psql UNUTAR kontejnera — bez asyncio.run(), koji bi se sudario sa
       event loop-om pytest-asyncio.
    2) Pokreće `alembic upgrade head` kao poseban proces, sa env
       promjenljivim koje pokazuju na testcontainers bazu (env vars imaju
       prednost nad .env fajlom u pydantic-settings).
    """
    bootstrap_sql = (
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN "
        f"CREATE ROLE app_user WITH LOGIN PASSWORD '{APP_USER_PASSWORD}' NOBYPASSRLS; "
        "END IF; END $$; "
        "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
    )
    exit_code, output = postgres_container.exec(
        [
            "psql",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            postgres_container.username,
            "-d",
            postgres_container.dbname,
            "-c",
            bootstrap_sql,
        ]
    )
    if exit_code != 0:
        raise RuntimeError(f"Bootstrap app_user role nije uspio: {output!r}")

    env = {
        **os.environ,
        "DATABASE_URL": _dsn(postgres_container, "app_user", APP_USER_PASSWORD),
        "ADMIN_DATABASE_URL": _dsn(
            postgres_container, postgres_container.username, postgres_container.password
        ),
        "REDIS_URL": "redis://localhost:6379/0",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ROOT_USER": "test",
        "MINIO_ROOT_PASSWORD": "test",
        "JWT_SECRET_KEY": JWT_TEST_SECRET,
    }
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Alembic migracija nije uspjela:\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
    return postgres_container


@pytest_asyncio.fixture(scope="session")
async def admin_engine(migrated_database: PostgresContainer) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_engine(
        _settings_for(
            _dsn(migrated_database, migrated_database.username, migrated_database.password)
        )
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def app_user_engine(
    migrated_database: PostgresContainer,
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_engine(
        _settings_for(_dsn(migrated_database, "app_user", APP_USER_PASSWORD))
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def admin_session(admin_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with create_session_factory(admin_engine)() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def app_user_session(app_user_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with create_session_factory(app_user_engine)() as session:
        yield session
        await session.rollback()


async def set_institution_context(session: AsyncSession, institution_id: object) -> None:
    """
    Ekvivalent caf.db.rls.set_tenant_context. VAŽNO: kontekst je
    transakcijski (is_local=true) — nestaje na commit/rollback, pa se mora
    postaviti ponovo na početku SVAKE nove transakcije. To je namjerno
    ponašanje produkcije (konekcija iz pool-a ne smije ponijeti tuđi
    tenant kontekst), i testovi ga moraju poštovati.
    """
    await session.execute(
        text("SELECT set_config('app.current_institution_id', :iid, true)"),
        {"iid": str(institution_id)},
    )
