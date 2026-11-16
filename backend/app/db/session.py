from collections.abc import Generator
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from backend.app.core.config import settings

class Base(DeclarativeBase):
    pass

def _get_engine():
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        return engine
    except Exception:
        # Ensure storage directory exists
        Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
        fallback_url = f"sqlite:///{Path(settings.storage_root).resolve() / 'eyeris_fallback.db'}"
        return create_engine(fallback_url, connect_args={"check_same_thread": False})

engine = _get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    import backend.app.db.models  # ensure models are registered
    Base.metadata.create_all(bind=engine)

# Auto-initialize tables
try:
    init_db()
except Exception:
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
