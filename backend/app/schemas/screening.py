from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from backend.app.schemas.prediction import GradePredictionResult, LesionSegmentationResult, QualityAssessmentResult
from backend.app.schemas.explanation import GradCAMResult

class ScreeningStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED_QUALITY = "rejected_quality"

class ClinicalDecision(BaseModel):
    referral_recommended: bool
    urgency: str
    rationale: str
    action_required: str

class ScreeningResponse(BaseModel):
    case_id: str
    timestamp: datetime
    status: ScreeningStatus
    quality: QualityAssessmentResult
    classification: GradePredictionResult | None = None
    segmentation: LesionSegmentationResult | None = None
    explainability: GradCAMResult | None = None
    clinical_decision: ClinicalDecision
    disclaimer: str = "Research screening prototype only. Not a certified diagnostic medical device."

class ScreeningDetailResponse(BaseModel):
    case_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    image_url: str | None = None
    quality_gradable: bool | None = None
    overall_quality_score: float | None = None
    predicted_grade: int | None = None
    grade_name: str | None = None
    calibrated_confidence: float | None = None
    uncertainty_score: float | None = None
    referable: bool | None = None
    urgency: str | None = None
    rationale: str | None = None
    action_required: str | None = None
    model_version: str | None = None
    execution_time_ms: int | None = None

class ScreeningReportResponse(BaseModel):
    report_id: str
    case_id: str
    generated_at: datetime
    patient_identifier: str | None = None
    summary_markdown: str
    screening_result: ScreeningResponse
