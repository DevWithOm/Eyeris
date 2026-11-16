from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None

class BaseAPIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: ErrorDetail | None = None

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    app_name: str = "retina-screening"
    environment: str = "development"
    database_connected: bool = True
