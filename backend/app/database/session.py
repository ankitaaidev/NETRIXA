"""
Database engine and session management.

DEMO_MODE note: this module is safe to import even with DATABASE_URL unset —
engine creation is lazy (deferred to get_engine()/get_db()) so importing
models or running the app in demo mode without Postgres does not crash.
Actual DB-dependent endpoints will surface a clear error only when used.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not configured. Set it in .env to use database features. "
                "The app itself still runs in DEMO_MODE without it."
            )
        _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, future=True)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a request-scoped session, always closed after."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope():
    """Context-manager form for scripts (seeding, tests) outside of FastAPI's DI."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
