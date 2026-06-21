import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_DB = DATABASE_URL.startswith("postgresql")

Base = declarative_base()
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if USE_DB else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if USE_DB else None


def init_db() -> None:
    if USE_DB and engine is not None:
        Base.metadata.create_all(bind=engine)


@contextmanager
def db_session():
    if not USE_DB or SessionLocal is None:
        raise RuntimeError("Database session unavailable. Set DATABASE_URL for PostgreSQL.")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
