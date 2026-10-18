"""
Database connection management for Project Atlas.
Supports MySQL in production/Docker with graceful fallback to local SQLite.
Provides regular session and safe read-only query executors.
"""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.models import Base

logger = logging.getLogger(__name__)

def create_db_engine(url: str):
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)

# Main engine
try:
    engine = create_db_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    logger.warning(f"Failed to connect to primary DB ({settings.DATABASE_URL}): {e}. Falling back to SQLite.")
    sqlite_url = f"sqlite:///{settings.BASE_DIR / 'atlas.db'}"
    engine = create_db_engine(sqlite_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Read-only engine for SQL tool
try:
    readonly_engine = create_db_engine(settings.READONLY_DATABASE_URL)
    ReadOnlySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=readonly_engine)
except Exception:
    readonly_engine = engine
    ReadOnlySessionLocal = SessionLocal

def init_db():
    """Initializes tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for DB sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
