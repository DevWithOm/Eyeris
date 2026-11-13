from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes.health import router as health_router
from backend.app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0",
              description="Research screening-support API; not a diagnostic device.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=False, allow_methods=["GET", "POST"],
                   allow_headers=["*"])
app.include_router(health_router, prefix="/api")

@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs"}
