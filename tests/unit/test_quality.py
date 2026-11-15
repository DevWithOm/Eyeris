"""Unit tests for retinal image quality assessment module."""

from pathlib import Path
import cv2
import numpy as np
import pytest
from PIL import Image

from src.vision.quality import (
    FOVStatus,
    QualityConfig,
    QualityReason,
    QualityStatus,
    RetinalQualityAssessor,
    assess_quality,
)

DATASET_SAMPLE = Path("data/raw/IDRiD/A. Segmentation/1. Original Images/a. Training Set/IDRiD_01.jpg")


def _generate_synthetic_fundus(
    width: int = 600,
    height: int = 600,
    center_color: int = 120,
    blur: bool = False,
    dark: bool = False,
    glare: bool = False,
    radius_ratio: float = 0.42,
) -> np.ndarray:
    """Helper to generate controllable synthetic fundus images."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    center = (width // 2, height // 2)
    radius = int(min(width, height) * radius_ratio)

    if dark:
        base_color = 25
    elif glare:
        base_color = center_color
    else:
        base_color = center_color

    # Draw circular fundus disc with mild radial shading
    cv2.circle(img, center, radius, (base_color // 3, int(base_color * 0.9), base_color), -1)

    # Add sharp simulated blood vessels/edges inside the fundus
    if not dark:
        # Multiple vessel branches
        cv2.line(img, (center[0] - radius // 2, center[1]), (center[0] + radius // 2, center[1]), (20, 40, 180), 3)
        cv2.line(img, (center[0], center[1] - radius // 2), (center[0], center[1] + radius // 2), (15, 35, 170), 2)
        cv2.line(img, (center[0] - 50, center[1] - 50), (center[0] + 50, center[1] + 50), (18, 38, 175), 2)
        cv2.circle(img, (center[0] + radius // 3, center[1]), 22, (80, 220, 240), -1)  # Optic disc
        cv2.circle(img, (center[0] - radius // 4, center[1]), 12, (10, 20, 90), -1)   # Fovea

    if glare:
        # Add saturated glare spot
        cv2.circle(img, (center[0] - 40, center[1] - 40), 55, (255, 255, 255), -1)

    if blur:
        img = cv2.GaussianBlur(img, (51, 51), sigmaX=15)

    return img


def test_quality_output_structure():
    """Verify that output contains all required fields and valid types."""
    synthetic = _generate_synthetic_fundus()
    res = assess_quality(synthetic)

    # Required output fields per specification
    required_keys = {
        "quality_score",
        "status",
        "blur_score",
        "illumination_score",
        "field_of_view_status",
        "reason_codes",
        "recapture_suggestion",
        "is_gradable",
        "details",
    }
    assert required_keys.issubset(res.keys())

    assert isinstance(res["quality_score"], float)
    assert 0.0 <= res["quality_score"] <= 1.0
    assert res["status"] in {QualityStatus.GRADABLE.value, QualityStatus.REVIEW_REQUIRED.value, QualityStatus.UNGRADABLE.value}
    assert isinstance(res["blur_score"], float)
    assert 0.0 <= res["blur_score"] <= 1.0
    assert isinstance(res["illumination_score"], float)
    assert 0.0 <= res["illumination_score"] <= 1.0
    assert res["field_of_view_status"] in {FOVStatus.ADEQUATE.value, FOVStatus.PARTIAL_CLIPPED.value, FOVStatus.INSUFFICIENT.value}
    assert isinstance(res["reason_codes"], list)


def test_gradable_synthetic_fundus():
    """Verify that a sharp, well-exposed, well-centered synthetic image is GRADABLE."""
    synthetic = _generate_synthetic_fundus(blur=False, dark=False, glare=False)
    res = assess_quality(synthetic)

    assert res["status"] == QualityStatus.GRADABLE.value
    assert res["is_gradable"] is True
    assert res["quality_score"] >= 0.70
    assert res["field_of_view_status"] == FOVStatus.ADEQUATE.value
    assert len(res["reason_codes"]) == 0
    assert res["recapture_suggestion"] is None


def test_blur_detection_ungradable():
    """Verify that severe blur flags SEVERE_BLUR and marks the image UNGRADABLE."""
    blurred = _generate_synthetic_fundus(blur=True)
    res = assess_quality(blurred)

    assert res["status"] == QualityStatus.UNGRADABLE.value
    assert res["is_gradable"] is False
    assert QualityReason.SEVERE_BLUR.value in res["reason_codes"]
    assert res["blur_score"] < 0.30
    assert res["recapture_suggestion"] is not None
    assert "blur" in res["recapture_suggestion"].lower()


def test_underexposure_detection():
    """Verify that deeply dark fundus triggers UNDEREXPOSED and review/ungradable."""
    dark_img = _generate_synthetic_fundus(dark=True)
    res = assess_quality(dark_img)

    assert QualityReason.UNDEREXPOSED.value in res["reason_codes"]
    assert res["status"] in (QualityStatus.UNGRADABLE.value, QualityStatus.REVIEW_REQUIRED.value)
    assert res["recapture_suggestion"] is not None
    assert "dark" in res["recapture_suggestion"].lower() or "underexposed" in res["recapture_suggestion"].lower()


def test_overexposure_glare_detection():
    """Verify that saturated flash glare triggers OVEREXPOSED."""
    glare_img = _generate_synthetic_fundus(glare=True)
    res = assess_quality(glare_img)

    assert QualityReason.OVEREXPOSED.value in res["reason_codes"]
    assert res["recapture_suggestion"] is not None
    assert "glare" in res["recapture_suggestion"].lower() or "overexposure" in res["recapture_suggestion"].lower()


def test_fov_too_small():
    """Verify that an extremely small field of view is classified as INSUFFICIENT and UNGRADABLE."""
    small_fov_img = _generate_synthetic_fundus(radius_ratio=0.15)  # Area ~7% of canvas
    res = assess_quality(small_fov_img)

    assert res["field_of_view_status"] == FOVStatus.INSUFFICIENT.value
    assert QualityReason.FOV_TOO_SMALL.value in res["reason_codes"]
    assert res["status"] == QualityStatus.UNGRADABLE.value


def test_blank_image():
    """Verify that a uniform blank image is rejected safely."""
    blank = np.zeros((600, 600, 3), dtype=np.uint8)
    res = assess_quality(blank)

    assert res["status"] == QualityStatus.UNGRADABLE.value
    assert res["quality_score"] == 0.0
    assert QualityReason.BLANK_IMAGE.value in res["reason_codes"] or QualityReason.FOV_TOO_SMALL.value in res["reason_codes"]


def test_unreadable_and_missing_file():
    """Verify safe error handling for missing or unreadable files without raising unhandled exceptions."""
    res_missing = assess_quality("non_existent_retina_image_9999.jpg")
    assert res_missing["status"] == QualityStatus.UNGRADABLE.value
    assert res_missing["quality_score"] == 0.0
    assert QualityReason.FILE_NOT_FOUND.value in res_missing["reason_codes"]

    # Invalid dimension input
    tiny_img = np.zeros((100, 100, 3), dtype=np.uint8)
    res_tiny = assess_quality(tiny_img)
    assert res_tiny["status"] == QualityStatus.UNGRADABLE.value
    assert QualityReason.INVALID_DIMENSIONS.value in res_tiny["reason_codes"]


def test_pil_image_input():
    """Verify that PIL Image instances are handled interchangeably with numpy arrays and paths."""
    synthetic_cv = _generate_synthetic_fundus()
    synthetic_pil = Image.fromarray(cv2.cvtColor(synthetic_cv, cv2.COLOR_BGR2RGB))

    res_cv = assess_quality(synthetic_cv)
    res_pil = assess_quality(synthetic_pil)

    assert res_cv["status"] == res_pil["status"]
    assert abs(res_cv["quality_score"] - res_pil["quality_score"]) < 0.05


def test_real_idrid_sample():
    """Verify quality assessment execution on available real clinical sample."""
    if not DATASET_SAMPLE.exists():
        pytest.skip("IDRiD sample image not available")

    res = assess_quality(DATASET_SAMPLE)
    assert "quality_score" in res
    assert res["status"] in {QualityStatus.GRADABLE.value, QualityStatus.REVIEW_REQUIRED.value}
    assert res["blur_score"] > 0.50
    assert res["illumination_score"] > 0.70


def test_configurable_thresholds():
    """Verify that custom QualityConfig thresholds successfully alter status thresholds."""
    synthetic = _generate_synthetic_fundus()

    # With ultra-strict blur requirement, even a sharp synthetic image triggers review
    strict_config = QualityConfig(blur_review_threshold=999.0)
    res_strict = assess_quality(synthetic, config=strict_config)

    assert QualityReason.MARGINAL_BLUR.value in res_strict["reason_codes"]
    assert res_strict["status"] != QualityStatus.GRADABLE.value
