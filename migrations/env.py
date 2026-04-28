import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- Chargement de la configuration Alembic ---
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Injection de l'URL depuis nos settings (lit le .env) ---
# Doit être fait AVANT d'importer les modèles pour éviter les imports circulaires
from app.config import settings  # noqa: E402

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# --- Import de la Base + tous les modèles pour l'autogenerate ---
# app.models.__init__ importe tous les modèles → Base.metadata est complet
from app.db.postgres import Base  # noqa: E402
import app.models  # noqa: E402, F401  — side-effect import : peuple Base.metadata

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Mode OFFLINE — génère le SQL sans connexion réelle
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    # Pour offline on utilise le driver sync (psycopg2) : on retire +asyncpg
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Mode ONLINE async — utilise asyncpg via SQLAlchemy async
# ---------------------------------------------------------------------------
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,      # détecte les changements de type de colonne
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
