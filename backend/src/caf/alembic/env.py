"""
Alembic environment — koristi async engine i čita DATABASE_URL iz
aplikacione konfiguracije (caf.core.config), ne iz alembic.ini, da
migracije i runtime app uvijek gledaju istu konekcionu logiku.

Database & Security Agent (CLAUDE.md Sekcija 8.2). Konkretni modeli se
uvoze ovde (import caf.models...) čim postoje (Korak 4), da
`target_metadata` omogući autogenerate.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from caf.core.config import get_settings
from caf.db.base import Base

import caf.models  # noqa: F401 — uvoz registruje sve tabele u Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_settings = get_settings()
# Migracije idu kao vlasnik baze (ADMIN_DATABASE_URL), ne kao app_user —
# app_user nema DDL prava po dizajnu (infra/postgres/init-rls.sh).
config.set_main_option("sqlalchemy.url", _settings.migration_database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
