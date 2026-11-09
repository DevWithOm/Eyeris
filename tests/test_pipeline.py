"""
Unit and integration sanity tests for Diabetic Retinopathy pipeline components.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from PIL import Image
import torch

from src.data import (
    crop_fundus_borders,
    get_transforms,
    RetinopathyDataset,
    compute_class_weights,
    create_stratified_splits
)
from src.model import build_efficientnet_b0, get_loss_criterion
from src.evaluate import compute_comprehensive_metrics
from src.predict import predict_retinopathy


def test_crop_fundus_borders():
    # Create black canvas with colored center circle
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    arr[50:250, 50:250] = 180
    img = Image.fromarray(arr)
    cropped = crop_fundus_borders(img)
    assert cropped.size[0] < 300 and cropped.size[1] < 300
    print("✅ test_crop_fundus_borders passed.")


def test_stratified_splits():
    # Synthetic dataset with 5 classes
    data = []
    for grade in range(5):
        for i in range(100):
            data.append({"id_code": f"img_{grade}_{i}", "diagnosis": grade})
    df = pd.DataFrame(data)

    train_df, val_df, test_df = create_stratified_splits(
        df, target_ratios=(0.70, 0.15, 0.15), seed=42
    )

    assert len(train_df) == 350
    assert len(val_df) == 75
    assert len(test_df) == 75

    # Check zero overlap
    assert len(set(train_df["id_code"]) & set(val_df["id_code"])) == 0
    assert len(set(train_df["id_code"]) & set(test_df["id_code"])) == 0
    assert len(set(val_df["id_code"]) & set(test_df["id_code"])) == 0

    # Check all classes present
    assert set(train_df["diagnosis"]) == {0, 1, 2, 3, 4}
    assert set(val_df["diagnosis"]) == {0, 1, 2, 3, 4}
    assert set(test_df["diagnosis"]) == {0, 1, 2, 3, 4}
    print("✅ test_stratified_splits passed.")


def test_class_weights():
    df = pd.DataFrame({"diagnosis": [0, 0, 0, 0, 1, 2, 2, 3, 4]})
    weights = compute_class_weights(df, num_classes=5)
    assert len(weights) == 5
    assert weights[3] > weights[0]  # Minority class has higher weight
    print("✅ test_class_weights passed.")


def test_model_forward():
    model = build_efficientnet_b0(num_classes=5, pretrained=False)
    dummy_input = torch.randn(2, 3, 224, 224)
    logits = model(dummy_input)
    assert logits.shape == (2, 5)
    print("✅ test_model_forward passed.")


def test_metrics_computation():
    y_true = [0, 1, 2, 3, 4, 0, 2]
    y_pred = [0, 1, 2, 2, 4, 0, 1]
    metrics = compute_comprehensive_metrics(y_true, y_pred, referable_threshold=2)

    assert "overall_accuracy" in metrics
    assert "macro_f1" in metrics
    assert "referable_dr" in metrics
    assert 0.0 <= metrics["referable_dr"]["sensitivity"] <= 1.0
    assert 0.0 <= metrics["referable_dr"]["specificity"] <= 1.0
    print("✅ test_metrics_computation passed.")


def test_predict_function():
    model = build_efficientnet_b0(num_classes=5, pretrained=False)
    dummy_img = Image.new("RGB", (224, 224), color=(100, 50, 30))
    res = predict_retinopathy(dummy_img, model, device=torch.device("cpu"), crop_borders=False)

    assert "predicted_grade" in res
    assert res["predicted_grade"] in range(5)
    assert "is_referable" in res
    assert "confidence" in res
    assert len(res["class_probabilities"]) == 5
    print("✅ test_predict_function passed.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    test_crop_fundus_borders()
    test_stratified_splits()
    test_class_weights()
    test_model_forward()
    test_metrics_computation()
    test_predict_function()
    print("\n🎉 ALL UNIT SANITY TESTS PASSED SUCCESSFULLY!")
