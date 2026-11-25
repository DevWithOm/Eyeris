from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.screenings import router as screenings_router
from backend.app.core.config import settings
from backend.app.db.session import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization skipped: {e}")
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Research screening-support API; not a diagnostic medical device.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# API v1 Router Registration
app.include_router(health_router, prefix="/api/v1")
app.include_router(screenings_router, prefix="/api/v1")

# Backward compatibility / legacy endpoints
app.include_router(health_router, prefix="/api")

@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "api_v1": "/api/v1",
        "disclaimer": "Research screening prototype only. Not a certified diagnostic medical device.",
    }
