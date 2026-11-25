import os
from collections.abc import Generator
from fastapi import HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from backend.app.core.config import settings

class Base(DeclarativeBase):
    pass

_engine = None
_SessionLocal = None

def get_engine():
    global _engine, _SessionLocal
    # Allow dynamic environment override for test fixtures
    db_url = os.environ.get("DATABASE_URL", settings.database_url)
    if _engine is None or str(_engine.url) != db_url:
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            _engine = create_engine(db_url, connect_args=connect_args)
        else:
            # PostgreSQL / External DB: Never silently fallback to SQLite!
            _engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine

def get_sessionmaker():
    global _SessionLocal
    get_engine()
    return _SessionLocal

def init_db():
    """
    Initializes database schema.
    """
    import backend.app.db.models  # ensure models are registered
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

def check_db_connection() -> bool:
    """
    Probes database health safely without raising unhandled exceptions.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy session.
    If database is unavailable, raises HTTP 503 rather than silently failing.
    """
    session_factory = get_sessionmaker()
    db = session_factory()
    try:
        # Verify connection is live
        db.execute(text("SELECT 1"))
        yield db
    except (OperationalError, SQLAlchemyError) as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database service is unavailable. Please verify database connectivity: {e}",
        ) from e
    finally:
        db.close()
