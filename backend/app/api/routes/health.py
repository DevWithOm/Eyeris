from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.schemas.response import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok",
        version="0.1.0",
        app_name=settings.app_name,
        environment=settings.app_env,
        database_connected=db_ok,
    )
