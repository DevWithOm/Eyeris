from pathlib import Path
from PIL import Image
import numpy as np
import pytest

from integration.pipeline import analyse_case


def _create_synthetic_fundus_image(file_path: Path, width: int = 512, height: int = 512) -> None:
    """Creates a synthetic retinal fundus photograph for pipeline verification."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    center_y, center_x = height // 2, width // 2
    radius = int(min(width, height) * 0.45)

    y, x = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    fundus_mask = dist_from_center <= radius

    # Retinal orange/red background
    arr[fundus_mask] = [180, 80, 30]

    # Simulated optic disc
    disc_mask = np.sqrt((x - (center_x + radius // 3)) ** 2 + (y - center_y) ** 2) <= (radius * 0.15)
    arr[disc_mask] = [240, 210, 100]

    # Simulated blood vessels
    arr[center_y - 2 : center_y + 2, center_x - radius // 2 : center_x + radius // 2] = [100, 20, 10]

    img = Image.fromarray(arr)
    img.save(file_path)


def test_complete_screening(tmp_path: Path):
    """End-to-end integration test verifying complete screening across all modules:
    Quality Assessment -> DR Classification -> U-Net Segmentation -> Grad-CAM & Calibration -> Clinical Decision.
    """
    test_img = tmp_path / "complete_screening_test.png"
    _create_synthetic_fundus_image(test_img)

    result = analyse_case(str(test_img), config={"case_id": "EYE-E2E001"})

    # 1. Pipeline metadata and contract structure
    assert "case_id" in result
    assert result["case_id"] == "EYE-E2E001"
    assert "timestamp" in result
    assert result["status"] == "completed"
    assert "disclaimer" in result

    # 2. Quality Assessment stage
    assert "quality" in result
    qc = result["quality"]
    assert qc["is_gradable"] is True
    assert 0.0 <= qc["overall_quality_score"] <= 1.0
    assert "metrics" in qc
    assert "sharpness_score" in qc["metrics"]
    assert "illumination_score" in qc["metrics"]

    # 3. DR Classification stage
    assert "classification" in result
    cls = result["classification"]
    assert cls is not None
    assert cls["predicted_grade"] in [0, 1, 2, 3, 4]
    assert isinstance(cls["grade_name"], str)
    assert "raw_probabilities" in cls
    assert isinstance(cls["referable_dr"], bool)

    # 4. Segmentation stage
    assert "segmentation" in result
    seg = result["segmentation"]
    assert seg is not None
    assert "lesions_detected" in seg
    assert "lesion_areas" in seg

    # 5. Explainability & Calibration stage
    assert "explainability" in result
    expl = result["explainability"]
    assert expl is not None
    assert "target_class" in expl
    assert 0.0 <= expl["calibrated_confidence"] <= 1.0
    assert 0.0 <= expl["uncertainty_score"] <= 1.0

    # 6. Clinical Decision Engine
    assert "clinical_decision" in result
    decision = result["clinical_decision"]
    assert isinstance(decision["referral_recommended"], bool)
    assert decision["urgency"] in [
        "annual_screening",
        "routine_monitoring",
        "routine_referral",
        "prompt_referral",
        "urgent_referral",
        "urgent_review",
        "manual_review",
        "recapture_required",
    ]
    assert "rationale" in decision
    assert "action_required" in decision
