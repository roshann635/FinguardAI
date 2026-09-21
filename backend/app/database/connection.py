import logging
import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Locate default SQLite demo DB
ROOT_DIR = Path(__file__).parent.parent.parent.parent
SQLITE_PATH = ROOT_DIR / "data" / "finguard_demo.sqlite"
SQLITE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"


def _create_database_engine():
    db_url = settings.database_url

    # Check if database is SQLite or PostgreSQL
    if db_url.startswith("sqlite"):
        eng = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
        )
        _setup_sqlite_listeners(eng)
        return eng

    # If PostgreSQL, test connection with a 1-second timeout
    try:
        test_eng = create_engine(
            db_url,
            connect_args={"connect_timeout": 1},
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        with test_eng.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        logger.info("Connected successfully to PostgreSQL database")
        return test_eng
    except Exception as exc:
        logger.warning(
            f"PostgreSQL connection failed ({exc}). Falling back to local SQLite demo database at {SQLITE_PATH}"
        )
        eng = create_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False},
        )
        _setup_sqlite_listeners(eng)
        return eng


def _setup_sqlite_listeners(eng):
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


engine = _create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

