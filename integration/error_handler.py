from enum import Enum
from typing import Any

class ErrorCode(str, Enum):
    INVALID_IMAGE_FORMAT = "INVALID_IMAGE_FORMAT"
    IMAGE_NOT_FOUND = "IMAGE_NOT_FOUND"
    IMAGE_UNGRADABLE = "IMAGE_UNGRADABLE"
    QUALITY_CHECK_FAILED = "QUALITY_CHECK_FAILED"
    PREPROCESSING_FAILED = "PREPROCESSING_FAILED"
    CLASSIFIER_FAILED = "CLASSIFIER_FAILED"
    SEGMENTATION_FAILED = "SEGMENTATION_FAILED"
    EXPLAINABILITY_FAILED = "EXPLAINABILITY_FAILED"
    DECISION_ENGINE_FAILED = "DECISION_ENGINE_FAILED"
    STORAGE_ERROR = "STORAGE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class ScreeningException(Exception):
    def __init__(self, code: ErrorCode, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

class QualityRejectionError(ScreeningException):
    def __init__(self, message: str, reasons: list[str], quality_score: float):
        super().__init__(
            code=ErrorCode.IMAGE_UNGRADABLE,
            message=message,
            details={"reasons": reasons, "quality_score": quality_score},
        )
        self.reasons = reasons
        self.quality_score = quality_score
