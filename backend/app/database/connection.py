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
    import calendar
    import datetime

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        def date_trunc(trunc, val):
            if not val:
                return None
            val_str = str(val)[:10]
            if trunc.lower() == "month":
                return val_str[:7] + "-01"
            elif trunc.lower() == "year":
                return val_str[:4] + "-01-01"
            elif trunc.lower() == "quarter":
                m = int(val_str[5:7])
                qm = ((m - 1) // 3) * 3 + 1
                return f"{val_str[:4]}-{qm:02d}-01"
            elif trunc.lower() == "week":
                dt = datetime.date.fromisoformat(val_str)
                return (dt - datetime.timedelta(days=dt.weekday())).isoformat()
            return val_str

        def extract(field, val):
            if not val:
                return 0
            val_str = str(val)[:10]
            dt = datetime.date.fromisoformat(val_str)
            if field.lower() == "month":
                return dt.month
            elif field.lower() == "year":
                return dt.year
            elif field.lower() == "day":
                return dt.day
            return 0

        dbapi_connection.create_function("date_trunc", 2, date_trunc)
        dbapi_connection.create_function("DATE_TRUNC", 2, date_trunc)
        dbapi_connection.create_function("extract", 2, extract)
        dbapi_connection.create_function("EXTRACT", 2, extract)



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

