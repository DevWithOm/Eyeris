import io
from pathlib import Path
from PIL import Image
from integration.pipeline import analyse_case

def test_pipeline_analyse_case_with_mock(tmp_path: Path):
    # Test with allow_mock=True
    test_img_path = tmp_path / "synthetic_fundus.png"
    img = Image.new("RGB", (512, 512), color=(120, 40, 20))
    img.save(test_img_path)

    result = analyse_case(str(test_img_path), config={"allow_mock": True})
    assert "case_id" in result
    assert result["status"] == "completed"
    assert result["quality"]["is_gradable"] is True
    assert result["classification"]["predicted_grade"] in [0, 1, 2, 3, 4]
    assert "clinical_decision" in result
    assert "disclaimer" in result

def test_pipeline_analyse_case_safe_default(tmp_path: Path):
    # Test with default allow_mock=False (safe production mode)
    test_img_path = tmp_path / "synthetic_fundus.png"
    img = Image.new("RGB", (512, 512), color=(120, 40, 20))
    img.save(test_img_path)

    result = analyse_case(str(test_img_path))
    assert "case_id" in result
    # When real models are present, pipeline completes; if absent, status is pending_review
    assert result["status"] in ["completed", "pending_review"]
    if result["status"] == "completed":
        assert result["classification"]["predicted_grade"] in [0, 1, 2, 3, 4]
        assert "clinical_decision" in result
    else:
        assert result["classification"] is None
        assert result["clinical_decision"]["urgency"] == "manual_review"

def test_pipeline_quality_rejection(tmp_path: Path):
    # Create an image that fails resolution check (<256x256)
    test_tiny_path = tmp_path / "tiny_image.png"
    img = Image.new("RGB", (64, 64), color=(0, 0, 0))
    img.save(test_tiny_path)

    result = analyse_case(str(test_tiny_path))
    assert result["status"] == "rejected_quality"
    assert result["quality"]["is_gradable"] is False
    assert result["clinical_decision"]["urgency"] == "recapture_required"
