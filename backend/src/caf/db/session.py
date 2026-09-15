"""
Async SQLAlchemy engine i session factory.

Database & Security Agent (CLAUDE.md Sekcija 7.2). Konekcija se PO
PRAVILU pravi kao `app_user` rola (bez BYPASSRLS, vidi
infra/postgres/init-rls.sh) — nikad kao superuser iz aplikacionog koda.

VAŽNO (naučeno u Koraku 2): engine/session factory se NE instanciraju na
nivou modula. Modulski singlton bi pozvao `get_settings()` pri svakom
importu ovog fajla — uključujući import u test fixtures koji namjerno
grade sopstveni engine protiv testcontainers baze — i pucao ako .env
nije prisutan u tom trenutku/tom radnom direktorijumu. Umjesto toga,
`get_engine()`/`get_session_factory()` su cached factory funkcije,
analogno `caf.core.config.get_settings()`.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from caf.core.config import Settings, get_settings


def create_engine(settings: Settings) -> AsyncEngine:
    """
    Factory umjesto modulskog singltona — testovi prave sopstveni engine
    protiv testcontainers baze, bez zavisnosti od produkcionog .env-a.
    """
    return create_async_engine(
        str(settings.database_url),
        echo=not settings.is_production,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@lru_cache
def get_engine() -> AsyncEngine:
    """
    Cached factory za runtime aplikaciju (FastAPI proces). Prvi poziv
    (tipično prvi request ka `get_db_session`) učitava Settings i pravi
    engine; svaki sledeći poziv vraća isti keširan engine — efektivno
    singlton, ali BEZ izvršavanja pri samom importu modula.
    """
    return create_engine(get_settings())


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(get_engine())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency. NE postavlja RLS tenant kontekst sama po sebi —
    to radi `caf.db.rls.set_tenant_context`, eksplicitno pozvan iz
    `api/deps.py` nakon što je JWT dekodiran. Razdvajanje je namjerno:
    ova funkcija zna samo za konekciju, ne za auth.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
