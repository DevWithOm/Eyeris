from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.db.session import check_db_connection
from backend.app.schemas.response import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
def health():
    db_ok = check_db_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version="0.1.0",
        app_name=settings.app_name,
        environment=settings.app_env,
        database_connected=db_ok,
    )
