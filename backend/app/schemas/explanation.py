from pydantic import BaseModel, Field

class GradCAMResult(BaseModel):
    gradcam_heatmap_path: str | None = None
    overlay_image_path: str | None = None
    target_class: int = Field(ge=0, le=4)
    calibrated_confidence: float = Field(ge=0.0, le=1.0)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    is_uncertain: bool = False
    calibration_method: str = "temperature_scaling"

class ExplanationDetailResponse(BaseModel):
    case_id: str
    target_class: int
    grade_name: str
    gradcam_heatmap_url: str | None = None
    overlay_image_url: str | None = None
    calibrated_confidence: float
    uncertainty_score: float
    is_uncertain: bool
    segmentation_mask_url: str | None = None
