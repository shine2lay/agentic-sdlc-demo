"""Database setup — shared Postgres between API and worker."""

from __future__ import annotations

import logging
import os

from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Render/Heroku use postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL == "sqlite://":
    # In-memory SQLite for testing: share one connection across threads
    engine = create_engine(
        DATABASE_URL, echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
elif DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, echo=False)


# Log DELETE and DROP statements for debugging data loss
@event.listens_for(engine, "before_cursor_execute")
def _log_destructive_sql(conn, cursor, statement, parameters, context, executemany):
    upper = statement.strip().upper()
    if upper.startswith(("DELETE", "DROP", "TRUNCATE")):
        logger.warning("DESTRUCTIVE SQL: %s  params=%s", statement[:200], parameters)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
