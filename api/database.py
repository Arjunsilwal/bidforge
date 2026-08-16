"""
SQLAlchemy Database Engine and Session Dependency.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from api.config import settings

# Handle SQLite connect_args if using local fallback
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Uses the SQLAlchemy 2.0 `DeclarativeBase` + `Mapped[...]` style so attribute
    access on an instance is typed as the Python value (`str`, `float`, ...) rather
    than `Column[...]`.
    """


def get_db() -> Generator[Session, None, None]:
    """Database session dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
