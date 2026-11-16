from typing import Any
from ai_models.common.labels import DR_GRADE_LABELS

def evaluate_screening_decision(
    quality: dict[str, Any],
    classification: dict[str, Any] | None,
    explainability: dict[str, Any] | None = None,
    segmentation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Evaluates research screening policy:
    1. If image quality is ungradable, mandate recapture / human review.
    2. If prediction uncertainty exceeds threshold, flag for clinician review.
    3. If grade is referable (>= 2), recommend clinical referral with urgency tiering.
    """
    # 1. Quality Gate
    if not quality.get("is_gradable", True) or quality.get("overall_quality_score", 1.0) < 0.6:
        reasons = quality.get("rejection_reasons", ["Poor image illumination or severe blur"])
        reasons_str = "; ".join(reasons)
        return {
            "referral_recommended": False,
            "urgency": "recapture_required",
            "rationale": f"Image quality insufficient for automated grading ({reasons_str}).",
            "action_required": "Recapture retinal fundus photograph following standard imaging protocol.",
        }

    if not classification:
        return {
            "referral_recommended": True,
            "urgency": "manual_review",
            "rationale": "Classification unavailable; clinical assessment required.",
            "action_required": "Ophthalmologist review required.",
        }

    grade = classification.get("predicted_grade", 0)
    grade_name = DR_GRADE_LABELS.get(grade, classification.get("grade_name", f"Grade {grade}"))
    calibrated_conf = explainability.get("calibrated_confidence", 0.8) if explainability else 0.8
    uncertainty = explainability.get("uncertainty_score", 0.0) if explainability else 0.0
    is_uncertain = explainability.get("is_uncertain", False) if explainability else False

    # 2. Uncertainty Escalation Gate
    if is_uncertain or uncertainty > 0.35:
        return {
            "referral_recommended": True,
            "urgency": "urgent_review",
            "rationale": f"High model uncertainty detected (uncertainty={uncertainty:.2f}, conf={calibrated_conf:.1%}) for predicted {grade_name}.",
            "action_required": "Escalate case for human clinician review due to model prediction ambiguity.",
        }

    # 3. Clinical Referral Tiers for Referable DR (Grades 2, 3, 4)
    if grade == 4:
        return {
            "referral_recommended": True,
            "urgency": "urgent_referral",
            "rationale": f"Proliferative Diabetic Retinopathy detected (calibrated confidence {calibrated_conf:.1%}). High risk of vision loss.",
            "action_required": "Urgent referral to retina specialist within 1–2 weeks for comprehensive evaluation and management.",
        }
    elif grade == 3:
        return {
            "referral_recommended": True,
            "urgency": "prompt_referral",
            "rationale": f"Severe Non-Proliferative Diabetic Retinopathy detected (calibrated confidence {calibrated_conf:.1%}).",
            "action_required": "Referral to ophthalmology clinic within 2–4 weeks.",
        }
    elif grade == 2:
        return {
            "referral_recommended": True,
            "urgency": "routine_referral",
            "rationale": f"Moderate Non-Proliferative Diabetic Retinopathy detected (calibrated confidence {calibrated_conf:.1%}).",
            "action_required": "Referral to ophthalmologist within 4–8 weeks for dilated eye examination.",
        }
    elif grade == 1:
        return {
            "referral_recommended": False,
            "urgency": "routine_monitoring",
            "rationale": f"Mild Non-Proliferative Diabetic Retinopathy detected (calibrated confidence {calibrated_conf:.1%}). Microaneurysms only.",
            "action_required": "Rescreen in 6–12 months. Reinforce glycemic and blood pressure control.",
        }
    else:  # Grade 0
        return {
            "referral_recommended": False,
            "urgency": "annual_screening",
            "rationale": f"No signs of Diabetic Retinopathy detected (calibrated confidence {calibrated_conf:.1%}).",
            "action_required": "Continue routine annual diabetic eye screening.",
        }
