import pytest
from datetime import datetime, timezone
from backend.app.schemas.prediction import (
    GradePredictionResult,
    LesionAreaSummary,
    LesionSegmentationResult,
    QualityAssessmentResult,
    QualityMetrics,
)
from backend.app.schemas.explanation import GradCAMResult
from backend.app.schemas.screening import ClinicalDecision, ScreeningResponse, ScreeningStatus

def test_quality_metrics_validation():
    metrics = QualityMetrics(
        sharpness_score=0.85,
        illumination_score=0.90,
        contrast_score=0.88,
        field_definition_score=0.95,
    )
    assert metrics.sharpness_score == 0.85

    with pytest.raises(Exception):
        # Exceeds max 1.0
        QualityMetrics(
            sharpness_score=1.5,
            illumination_score=0.9,
            contrast_score=0.8,
            field_definition_score=0.9,
        )

def test_screening_response_schema():
    resp = ScreeningResponse(
        case_id="EYE-TEST01",
        timestamp=datetime.now(timezone.utc),
        status=ScreeningStatus.COMPLETED,
        quality=QualityAssessmentResult(
            is_gradable=True,
            overall_quality_score=0.91,
            metrics=QualityMetrics(
                sharpness_score=0.85,
                illumination_score=0.92,
                contrast_score=0.89,
                field_definition_score=0.95,
            ),
        ),
        classification=GradePredictionResult(
            predicted_grade=2,
            grade_name="Moderate",
            raw_probabilities={"0": 0.05, "1": 0.15, "2": 0.70, "3": 0.07, "4": 0.03},
            referable_dr=True,
            model_version="test-v1",
        ),
        clinical_decision=ClinicalDecision(
            referral_recommended=True,
            urgency="routine_referral",
            rationale="Moderate DR detected",
            action_required="Referral within 4-6 weeks",
        ),
    )
    assert resp.case_id == "EYE-TEST01"
    assert resp.classification.predicted_grade == 2
    assert resp.clinical_decision.referral_recommended is True
