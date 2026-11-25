from sqlalchemy.orm import Session
from backend.app.db.models import ScreeningRecord
from backend.app.schemas.explanation import ExplanationDetailResponse

def get_explanation_for_case(case_id: str, db: Session) -> ExplanationDetailResponse | None:
    record = db.query(ScreeningRecord).filter(ScreeningRecord.case_id == case_id).first()
    if not record:
        return None

    target_class = record.predicted_grade if record.predicted_grade is not None else 0
    grade_name = record.grade_name or f"Grade {target_class}"
    confidence = record.calibrated_confidence if record.calibrated_confidence is not None else 0.85
    uncertainty = record.uncertainty_score if record.uncertainty_score is not None else 0.12
    is_uncertain = uncertainty > 0.35

    return ExplanationDetailResponse(
        case_id=record.case_id,
        target_class=target_class,
        grade_name=grade_name,
        gradcam_heatmap_url=f"/storage/cases/{record.case_id}/gradcam.png",
        overlay_image_url=f"/storage/cases/{record.case_id}/gradcam_overlay.png",
        calibrated_confidence=confidence,
        uncertainty_score=uncertainty,
        is_uncertain=is_uncertain,
        segmentation_mask_url=f"/storage/cases/{record.case_id}/lesion_mask.png",
    )
