import uuid
from typing import Any
from integration.model_orchestrator import orchestrate_screening

def analyse_case(image_path: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Proposed entry point specified in docs/integration_contract.md.
    Sequences quality assessment, grading, lesion segmentation, and explainability.
    """
    cfg = config or {}
    case_id = cfg.get("case_id") or f"EYE-{uuid.uuid4().hex[:8].upper()}"
    return orchestrate_screening(case_id=case_id, image_path=image_path, config=cfg)
