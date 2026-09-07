"""
One-shot helper to bring a fresh database up to the current schema.

In production this responsibility belongs to Alembic migrations (see
backend/alembic/). This module is intentionally kept simple and is used by:
  - tests (spin up schema against a real Postgres/PostGIS instance)
  - local bootstrap scripts / Phase 4 seeding

It does NOT replace Alembic — `alembic upgrade head` is the source of
truth for schema changes going forward; this is a convenience for fresh
environments and CI.
"""
from sqlalchemy import text

import app.models  # noqa: F401 - ensures every model is registered on Base.metadata
from app.database.geo_listeners import register_geo_listeners
from app.database.session import Base, get_engine


def init_db() -> None:
    engine = get_engine()

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()

    register_geo_listeners()
    Base.metadata.create_all(bind=engine)


def drop_all() -> None:
    """Used by tests to reset schema state between runs."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
