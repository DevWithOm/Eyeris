from datetime import datetime, timezone
from typing import Any
from ai_models.common.labels import DR_GRADE_LABELS

def format_pipeline_output(
    case_id: str,
    quality: dict[str, Any],
    classification: dict[str, Any] | None,
    segmentation: dict[str, Any] | None,
    explainability: dict[str, Any] | None,
    decision: dict[str, Any],
    status: str = "completed",
) -> dict[str, Any]:
    """
    Normalizes module outputs into the canonical schema agreed in the Interface Contract.
    """
    # Normalize grade name
    if classification and "grade_name" not in classification:
        grade = classification.get("predicted_grade", 0)
        classification["grade_name"] = DR_GRADE_LABELS.get(grade, f"Grade {grade}")

    return {
        "case_id": case_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "quality": quality,
        "classification": classification,
        "segmentation": segmentation,
        "explainability": explainability,
        "clinical_decision": decision,
        "disclaimer": "Research screening prototype only. Not a certified diagnostic medical device.",
    }
