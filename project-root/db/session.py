from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings


def db_configured() -> bool:
    return bool(getattr(settings, "DATABASE_URL", "").strip())


def persistence_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_DB_PERSISTENCE", False) and db_configured())


_connect_args = {}
if db_configured() and settings.DATABASE_URL.startswith("postgresql"):
    _connect_args["connect_timeout"] = int(getattr(settings, "DB_CONNECT_TIMEOUT_SECONDS", 5))

engine = create_engine(
    settings.DATABASE_URL,
    echo=getattr(settings, "DB_ECHO", False),
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
) if db_configured() else None

SessionLocal = (
    sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, future=True)
    if engine
    else None
)


@contextmanager
def session_scope() -> Iterator[Session]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
