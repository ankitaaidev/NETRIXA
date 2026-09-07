import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make the `app` package importable regardless of cwd Alembic is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.models  # noqa: E402 - registers every model on Base.metadata
from app.core.config import get_settings  # noqa: E402
from app.database.session import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Always source the DB URL from app settings (.env), never from alembic.ini,
# so the connection secret lives in exactly one place.
settings = get_settings()
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def include_object(object_, name, type_, reflected, compare_to):
    # Exclude PostGIS's own bookkeeping table from autogenerate diffs.
    if type_ == "table" and name == "spatial_ref_sys":
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
