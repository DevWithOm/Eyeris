import io
from pathlib import Path
from PIL import Image
from integration.pipeline import analyse_case

def test_pipeline_analyse_case(tmp_path: Path):
    # Create a synthetic 512x512 fundus image
    test_img_path = tmp_path / "synthetic_fundus.png"
    img = Image.new("RGB", (512, 512), color=(120, 40, 20))
    img.save(test_img_path)

    result = analyse_case(str(test_img_path))
    assert "case_id" in result
    assert result["status"] == "completed"
    assert result["quality"]["is_gradable"] is True
    assert result["classification"]["predicted_grade"] in [0, 1, 2, 3, 4]
    assert "clinical_decision" in result
    assert "disclaimer" in result

def test_pipeline_quality_rejection(tmp_path: Path):
    # Create an image that fails resolution check (<256x256)
    test_tiny_path = tmp_path / "tiny_image.png"
    img = Image.new("RGB", (64, 64), color=(0, 0, 0))
    img.save(test_tiny_path)

    result = analyse_case(str(test_tiny_path))
    assert result["status"] == "rejected_quality"
    assert result["quality"]["is_gradable"] is False
    assert result["clinical_decision"]["urgency"] == "recapture_required"
