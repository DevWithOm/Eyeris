from integration.decision_engine import evaluate_screening_decision

def test_decision_engine_quality_rejection():
    quality = {
        "is_gradable": False,
        "overall_quality_score": 0.42,
        "rejection_reasons": ["Severe blur detected"],
    }
    decision = evaluate_screening_decision(quality=quality, classification=None)
    assert decision["referral_recommended"] is False
    assert decision["urgency"] == "recapture_required"
    assert "recapture" in decision["action_required"].lower()

def test_decision_engine_uncertainty_escalation():
    quality = {"is_gradable": True, "overall_quality_score": 0.95}
    classification = {"predicted_grade": 1, "grade_name": "Mild"}
    explainability = {
        "calibrated_confidence": 0.45,
        "uncertainty_score": 0.55,
        "is_uncertain": True,
    }
    decision = evaluate_screening_decision(
        quality=quality,
        classification=classification,
        explainability=explainability,
    )
    assert decision["referral_recommended"] is True
    assert decision["urgency"] == "urgent_review"
    assert "uncertainty" in decision["rationale"].lower()

def test_decision_engine_proliferative_dr():
    quality = {"is_gradable": True, "overall_quality_score": 0.95}
    classification = {"predicted_grade": 4, "grade_name": "Proliferative DR"}
    explainability = {"calibrated_confidence": 0.92, "uncertainty_score": 0.08}
    decision = evaluate_screening_decision(
        quality=quality,
        classification=classification,
        explainability=explainability,
    )
    assert decision["referral_recommended"] is True
    assert decision["urgency"] == "urgent_referral"
    assert "1–2 weeks" in decision["action_required"]

def test_decision_engine_no_dr():
    quality = {"is_gradable": True, "overall_quality_score": 0.95}
    classification = {"predicted_grade": 0, "grade_name": "No DR"}
    explainability = {"calibrated_confidence": 0.98, "uncertainty_score": 0.02}
    decision = evaluate_screening_decision(
        quality=quality,
        classification=classification,
        explainability=explainability,
    )
    assert decision["referral_recommended"] is False
    assert decision["urgency"] == "annual_screening"
