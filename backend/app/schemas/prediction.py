from pydantic import BaseModel, Field

class QualityMetrics(BaseModel):
    sharpness_score: float = Field(ge=0.0, le=1.0)
    illumination_score: float = Field(ge=0.0, le=1.0)
    contrast_score: float = Field(ge=0.0, le=1.0)
    field_definition_score: float = Field(ge=0.0, le=1.0)

class QualityAssessmentResult(BaseModel):
    is_gradable: bool
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    metrics: QualityMetrics
    rejection_reasons: list[str] = Field(default_factory=list)

class GradePredictionResult(BaseModel):
    predicted_grade: int = Field(ge=0, le=4)
    grade_name: str
    raw_probabilities: dict[str, float]
    referable_dr: bool
    model_version: str

class LesionAreaSummary(BaseModel):
    hard_exudates_pixels: int = 0
    hemorrhages_pixels: int = 0
    microaneurysms_pixels: int = 0
    cotton_wool_spots_pixels: int = 0

class LesionSegmentationResult(BaseModel):
    lesions_detected: bool
    mask_shape: list[int] = Field(default_factory=lambda: [512, 512])
    lesion_areas: LesionAreaSummary = Field(default_factory=LesionAreaSummary)
    lesion_mask_path: str | None = None
    model_version: str = "unet-v1.0"
