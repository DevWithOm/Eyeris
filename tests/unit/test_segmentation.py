"""Unit tests for U-Net lesion segmentation architecture, loss, metrics, and inference."""

import os
from pathlib import Path
import cv2
import numpy as np
import pytest
import torch

from src.vision.segmentation.config import SegmentationConfig
from src.vision.segmentation.losses import CombinedSegmentationLoss, MaskedBCELoss, SoftDiceLoss
from src.vision.segmentation.metrics import calculate_segmentation_metrics
from src.vision.segmentation.model import UNet
from src.vision.segmentation.predict import generate_lesion_overlay, segment_lesions
from src.vision.segmentation.train import EarlyStopping

DATASET_SAMPLE = Path("data/raw/IDRiD/A. Segmentation/1. Original Images/a. Training Set/IDRiD_01.jpg")


def test_unet_forward_pass_dimensions():
    """Verify U-Net forward pass produces correct 4-channel lesion logits."""
    model = UNet(in_channels=3, num_classes=4, base_channels=16)
    x = torch.randn(2, 3, 128, 128)
    logits = model(x)

    assert logits.shape == (2, 4, 128, 128)
    assert not torch.isnan(logits).any()


def test_unet_predict_probabilities_and_masks():
    """Verify probability and binary mask predictions."""
    model = UNet(in_channels=3, num_classes=4, base_channels=16)
    x = torch.randn(1, 3, 64, 64)

    probs = model.predict_probabilities(x)
    assert probs.shape == (1, 4, 64, 64)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()

    masks = model.predict_masks(x, threshold=0.5)
    assert masks.shape == (1, 4, 64, 64)
    unique_vals = torch.unique(masks).tolist()
    for v in unique_vals:
        assert v in (0.0, 1.0)


def test_loss_masks_unannotated_channels():
    """CRITICAL TEST: Verify unavailable annotations do not contribute to loss or gradients."""
    loss_fn = CombinedSegmentationLoss(alpha=1.0, beta=1.0)

    # 2 samples, 4 classes, 32x32
    logits = torch.randn(2, 4, 32, 32, requires_grad=True)
    targets = torch.zeros(2, 4, 32, 32)
    targets[:, :, 10:20, 10:20] = 1.0  # Simulated foreground lesion

    # Sample 0 has all 4 classes annotated
    # Sample 1 has class 3 (SE) UNAVAILABLE/MISSING
    mask_valid = torch.tensor([[True, True, True, True], [True, True, True, False]])

    losses = loss_fn(logits, targets, mask_valid)
    total_loss = losses["loss"]
    total_loss.backward()

    # The gradient for Sample 1, Class 3 must be strictly ZERO because it was unavailable
    assert logits.grad is not None
    grad_sample1_class3 = logits.grad[1, 3]
    assert torch.all(grad_sample1_class3 == 0.0), "Unavailable annotation received non-zero gradients!"


def test_metrics_calculation():
    """Verify Dice and IoU calculation ignores unavailable classes."""
    targets = torch.zeros(2, 4, 32, 32)
    targets[:, :, 5:15, 5:15] = 1.0

    # Predictions match targets exactly for class 0, inverted for class 1
    probs = targets.clone()
    probs[:, 1] = 1.0 - probs[:, 1]

    mask_valid = torch.tensor([[True, True, True, True], [True, True, True, True]])

    metrics = calculate_segmentation_metrics(probs, targets, mask_valid, threshold=0.5)

    assert "dice_MA" in metrics and "iou_MA" in metrics
    assert metrics["dice_MA"] > 0.99  # Near perfect
    assert metrics["dice_HE"] < 0.10  # Completely wrong
    assert "mean_dice" in metrics
    assert "mean_iou" in metrics


def test_early_stopping():
    """Verify early stopping triggers after patience exhausted."""
    es = EarlyStopping(patience=3)

    assert es(0.50) is False
    assert es(0.55) is False  # Improvement
    assert es(0.54) is False  # Counter = 1
    assert es(0.53) is False  # Counter = 2
    assert es(0.52) is True   # Counter = 3 -> Triggered!
    assert es.early_stop is True


def test_overlay_generation():
    """Verify visual overlay generation blending and contours."""
    orig = np.zeros((100, 100, 3), dtype=np.uint8)
    orig[:] = (100, 100, 100)

    # 4 classes, each having a small lesion
    masks = np.zeros((4, 100, 100), dtype=np.uint8)
    masks[0, 10:20, 10:20] = 1  # MA
    masks[1, 30:50, 30:50] = 1  # HE

    overlay = generate_lesion_overlay(orig, masks)
    assert overlay.shape == orig.shape
    # Overlay should have modified pixel colors in lesion regions
    assert not np.array_equal(overlay[15, 15], orig[15, 15])
    # Unaffected regions should remain identical
    assert np.array_equal(overlay[90, 90], orig[90, 90])


def test_single_image_inference():
    """Verify single-image inference and integration contract."""
    # Synthetic image
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(img, (100, 100), 80, (100, 120, 150), -1)

    output_dir = "artifacts/evaluation/test_outputs"
    res = segment_lesions(
        image_input=img,
        config=SegmentationConfig(img_size=(128, 128), base_channels=16),
        output_dir=output_dir,
    )

    assert res["status"] == "SUCCESS"
    assert "lesion_detected" in res
    assert "lesion_counts" in res
    assert "lesion_area_ratio" in res
    assert "confidence" in res
    assert "mask_path" in res and res["mask_path"] is not None
    assert "overlay_path" in res and res["overlay_path"] is not None
    assert os.path.exists(res["mask_path"])
    assert os.path.exists(res["overlay_path"])


def test_config_serialization(tmp_path: Path):
    """Verify YAML configuration saving and loading."""
    cfg = SegmentationConfig(batch_size=8, learning_rate=1e-3, epochs=25)
    yaml_file = tmp_path / "test_config.yaml"
    cfg.save_yaml(yaml_file)

    loaded = SegmentationConfig.from_yaml(yaml_file)
    assert loaded.batch_size == 8
    assert loaded.learning_rate == 1e-3
    assert loaded.epochs == 25
    assert loaded.classes == ("MA", "HE", "EX", "SE")
