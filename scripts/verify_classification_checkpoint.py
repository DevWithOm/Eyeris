"""
Verification script for Member 1 Diabetic Retinopathy Classification Module.

Checks:
1. Loads artifacts/model_weights/best_model.pth with strict=True.
2. Checks parameter count (total and trainable).
3. Verifies model output shape is [1, 5].
4. Verifies predict_grade end-to-end on a test image.
"""

from pathlib import Path
import sys
import tempfile

import numpy as np
from PIL import Image
import torch

# Ensure repository root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai_models.classification.model import DEFAULT_CHECKPOINT_PATH, get_classification_model
from ai_models.classification.predict import predict_grade
from ai_models.classification.preprocessing import crop_fundus_borders, preprocess_fundus_image


def run_verification() -> bool:
    print("=" * 60)
    print("MEMBER 1: DR CLASSIFICATION CHECKPOINT VERIFICATION")
    print("=" * 60)

    # 1. Verify Checkpoint Existence
    checkpoint_path = DEFAULT_CHECKPOINT_PATH
    print(f"\n1. Target checkpoint: {checkpoint_path}")
    if not checkpoint_path.exists():
        print(f"ERROR: Checkpoint file not found at {checkpoint_path}")
        return False
    file_size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
    print(f"   Checkpoint size: {file_size_mb:.2f} MB")

    # 2. Load Model with strict=True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n2. Loading model on device: {device} with strict=True...")
    try:
        model = get_classification_model(checkpoint_path=checkpoint_path, device=device)
        print("   SUCCESS: Model instantiated and state_dict loaded with strict=True.")
    except Exception as e:
        print(f"   ERROR: Failed to load state_dict with strict=True: {e}")
        return False

    # 3. Parameter Counts
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n3. Model Parameters:")
    print(f"   Total parameters:     {total_params:,}")
    print(f"   Trainable parameters: {trainable_params:,}")

    # 4. Forward Pass Shape Verification
    print(f"\n4. Verifying forward pass output shape:")
    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    with torch.no_grad():
        output = model(dummy_input)
    print(f"   Input shape:  {list(dummy_input.shape)}")
    print(f"   Output shape: {list(output.shape)}")
    if list(output.shape) != [1, 5]:
        print(f"   ERROR: Expected output shape [1, 5], got {list(output.shape)}")
        return False
    print("   SUCCESS: Output tensor matches required [1, 5] shape.")

    # 5. Preprocessing & Crop Verification
    print(f"\n5. Verifying preprocessing and crop_fundus_borders:")
    # Create synthetic test fundus image with dark borders
    synthetic_arr = np.zeros((400, 400, 3), dtype=np.uint8)
    # Circle of retinal tissue in center
    y, x = np.ogrid[:400, :400]
    mask = (x - 200) ** 2 + (y - 200) ** 2 <= 150 ** 2
    synthetic_arr[mask] = [180, 70, 40]
    synthetic_img = Image.fromarray(synthetic_arr)

    cropped = crop_fundus_borders(synthetic_img, tol=10)
    print(f"   Original synthetic size: {synthetic_img.size}")
    print(f"   Cropped retinal size:    {cropped.size}")
    tensor = preprocess_fundus_image(synthetic_img, crop_borders=True)
    print(f"   Preprocessed tensor shape: {list(tensor.shape)}")
    if list(tensor.shape) != [1, 3, 224, 224]:
        print(f"   ERROR: Expected preprocessed tensor [1, 3, 224, 224], got {list(tensor.shape)}")
        return False

    # 6. End-to-End predict_grade verification
    print(f"\n6. Testing predict_grade(image_path) interface:")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
    try:
        synthetic_img.save(tmp_path)
        result = predict_grade(str(tmp_path), device=str(device))
        print("   Inference result:")
        for k, v in result.items():
            print(f"     - {k}: {v}")

        required_keys = [
            "predicted_grade",
            "grade_name",
            "probabilities",
            "raw_confidence",
            "model_name",
            "model_version",
        ]
        for key in required_keys:
            if key not in result:
                print(f"   ERROR: Missing required field '{key}' in prediction result.")
                return False
        if len(result["probabilities"]) != 5:
            print(f"   ERROR: Expected 5 probability values, got {len(result['probabilities'])}")
            return False

        print("   SUCCESS: predict_grade completed contract-compliant inference.")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    print("\n" + "=" * 60)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
