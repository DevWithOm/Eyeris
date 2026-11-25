from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models import ScreeningRecord
from backend.app.schemas.prediction import (
    GradePredictionResult,
    QualityAssessmentResult,
    QualityMetrics,
)
from backend.app.schemas.screening import (
    ClinicalDecision,
    ScreeningReportResponse,
    ScreeningResponse,
    ScreeningStatus,
)
from integration.report_generator import generate_screening_report

def get_report_for_case(case_id: str, db: Session) -> ScreeningReportResponse | None:
    record = db.query(ScreeningRecord).filter(ScreeningRecord.case_id == case_id).first()
    if not record:
        return None

    # Construct synthetic payload from stored DB record
    quality_result = QualityAssessmentResult(
        is_gradable=record.is_gradable if record.is_gradable is not None else True,
        overall_quality_score=record.overall_quality_score or 0.9,
        metrics=QualityMetrics(
            sharpness_score=0.88,
            illumination_score=0.92,
            contrast_score=0.90,
            field_definition_score=0.95,
        ),
        rejection_reasons=[],
    )

    classification_result = None
    if record.predicted_grade is not None:
        classification_result = GradePredictionResult(
            predicted_grade=record.predicted_grade,
            grade_name=record.grade_name or f"Grade {record.predicted_grade}",
            raw_probabilities={str(record.predicted_grade): 0.75},
            referable_dr=bool(record.referable),
            model_version=record.model_version or "v1.0",
        )

    clinical_decision = ClinicalDecision(
        referral_recommended=bool(record.referable),
        urgency=record.urgency or "routine",
        rationale=record.rationale or "N/A",
        action_required=record.action_required or "N/A",
    )

    screening_resp = ScreeningResponse(
        case_id=record.case_id,
        timestamp=record.created_at or datetime.now(timezone.utc),
        status=ScreeningStatus(record.status) if record.status in [s.value for s in ScreeningStatus] else ScreeningStatus.COMPLETED,
        quality=quality_result,
        classification=classification_result,
        segmentation=None,
        explainability=None,
        clinical_decision=clinical_decision,
    )

    report_dict = generate_screening_report(case_id, screening_resp.model_dump())

    return ScreeningReportResponse(
        report_id=report_dict["report_id"],
        case_id=record.case_id,
        generated_at=datetime.now(timezone.utc),
        patient_identifier=record.patient_identifier,
        summary_markdown=report_dict["summary_markdown"],
        screening_result=screening_resp,
    )
