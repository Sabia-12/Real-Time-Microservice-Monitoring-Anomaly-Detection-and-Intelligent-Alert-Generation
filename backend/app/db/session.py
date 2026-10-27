"""
Database session and connection management for SQLAlchemy.
"""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Default SQLite database path in backend/app/msm.db
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "msm.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# For SQLite, check_same_thread=False allows FastAPI multi-threaded requests
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session for requests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
