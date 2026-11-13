from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from backend.app.core.config import settings
engine = create_engine(settings.database_url, pool_pre_ping=True)
class Base(DeclarativeBase):
    pass
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
