"""Single-image inference and lesion overlay generator.

Provides:
- segment_lesions: Top-level inference function complying with integration contract.
- generate_lesion_overlay: Generates color-coded overlays on the original retinal image.
- save_prediction_artifacts: Saves predicted binary masks and summary metrics.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
from PIL import Image

from src.vision.segmentation.config import SegmentationConfig
from src.vision.segmentation.model import UNet

# Distinct visualization colors for each lesion class (BGR format for OpenCV)
LESION_COLORS: Dict[str, Tuple[int, int, int]] = {
    "MA": (0, 0, 255),       # Bright Red for Microaneurysms
    "HE": (0, 0, 139),       # Dark Crimson for Haemorrhages
    "EX": (0, 255, 255),     # Yellow for Hard Exudates
    "SE": (255, 255, 0),     # Cyan for Soft Exudates
}


def load_segmentation_model(
    checkpoint_path: Optional[str | Path] = None,
    config: Optional[SegmentationConfig] = None,
    device: Optional[str] = None,
) -> Tuple[Optional[UNet], str]:
    """Loads U-Net model from checkpoint if available, or returns uninitialized model."""
    cfg = config or SegmentationConfig()
    dev = device or cfg.device

    model = UNet(
        in_channels=cfg.in_channels,
        num_classes=cfg.num_classes,
        base_channels=cfg.base_channels,
        bilinear=cfg.bilinear,
    ).to(dev)
    model.eval()

    # Determine checkpoint path
    ckpt = checkpoint_path or os.path.join(cfg.checkpoint_dir, "best_model.pth")
    if os.path.exists(ckpt):
        try:
            checkpoint = torch.load(ckpt, map_location=dev, weights_only=False)
            if "model_state_dict" in checkpoint:
                model.load_state_dict(checkpoint["model_state_dict"])
            else:
                model.load_state_dict(checkpoint)
            return model, str(ckpt)
        except Exception as e:
            return model, f"uninitialized (load error: {e})"

    return model, "uninitialized (no checkpoint found)"


def preprocess_image_for_inference(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    img_size: Tuple[int, int] = (512, 512),
) -> Tuple[torch.Tensor, np.ndarray, Tuple[int, int]]:
    """Preprocesses a single retinal image for model inference.

    Returns:
        input_tensor: Normalized float tensor of shape (1, 3, H, W).
        original_bgr: Original image as BGR numpy array.
        original_dims: (orig_width, orig_height).
    """
    if isinstance(image_input, (str, Path)):
        original_bgr = cv2.imread(str(image_input))
        if original_bgr is None:
            raise FileNotFoundError(f"Cannot read image at {image_input}")
    elif isinstance(image_input, Image.Image):
        rgb = np.array(image_input.convert("RGB"))
        original_bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    elif isinstance(image_input, np.ndarray):
        original_bgr = image_input.copy()
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    orig_h, orig_w = original_bgr.shape[:2]

    # Resize for inference
    resized_bgr = cv2.resize(original_bgr, (img_size[1], img_size[0]), interpolation=cv2.INTER_LINEAR)
    rgb = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2RGB)

    # Normalize with standard ImageNet parameters
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)
    normalized = ((rgb / 255.0) - mean) / std

    # Shape: (1, 3, H, W)
    tensor = torch.from_numpy(normalized.transpose((2, 0, 1))).unsqueeze(0).float()
    return tensor, original_bgr, (orig_w, orig_h)


def generate_lesion_overlay(
    original_bgr: np.ndarray,
    predicted_masks: np.ndarray,
    classes: Sequence[str] = ("MA", "HE", "EX", "SE"),
    alpha: float = 0.45,
) -> np.ndarray:
    """Overlays color-coded lesion masks on the original retinal image.

    Args:
        original_bgr: Original BGR image (H, W, 3).
        predicted_masks: Binary numpy array of shape (C, H, W) in {0, 1}.
        classes: Tuple of class identifiers matching the C channels.
        alpha: Blending transparency factor for the lesion color overlay.

    Returns:
        Annotated BGR image with blended color overlays and contours.
    """
    overlay = original_bgr.copy()
    orig_h, orig_w = original_bgr.shape[:2]

    for c_idx, name in enumerate(classes):
        mask = predicted_masks[c_idx]
        if np.sum(mask) == 0:
            continue

        # Resize mask to original image dimensions if needed
        if mask.shape[:2] != (orig_h, orig_w):
            mask_resized = cv2.resize(
                mask.astype(np.uint8),
                (orig_w, orig_h),
                interpolation=cv2.INTER_NEAREST,
            )
        else:
            mask_resized = mask.astype(np.uint8)

        color = LESION_COLORS.get(name, (0, 255, 0))

        # Color blending on detected pixels
        colored_mask = np.zeros_like(original_bgr)
        colored_mask[mask_resized > 0] = color
        cv2.addWeighted(colored_mask, alpha, overlay, 1.0, 0, overlay)

        # Draw contour borders for sharp visibility
        contours, _ = cv2.findContours(mask_resized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, color, 1)

    return overlay


def segment_lesions(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    checkpoint_path: Optional[str | Path] = None,
    config: Optional[SegmentationConfig] = None,
    output_dir: Optional[str | Path] = "storage/segmentation_masks",
) -> Dict[str, Any]:
    """Runs lesion segmentation on a retinal image conforming to integration contract.

    Args:
        image_input: Path to image file, numpy array, or PIL Image.
        checkpoint_path: Optional path to trained model weights.
        config: Optional segmentation configuration overrides.
        output_dir: Directory where generated masks and visual overlays are saved.

    Returns:
        Structured result dictionary:
            - mask_path: str relative path to saved composite mask
            - overlay_path: str relative path to saved visual overlay
            - lesion_detected: bool
            - lesion_counts: dict with counts of detected lesions per class
            - lesion_area_ratio: float (total lesion area / retinal area)
            - confidence: float average confidence score
            - per_class_areas: dict with area fractions per class
            - status: 'SUCCESS'
    """
    cfg = config or SegmentationConfig()
    dev = cfg.device

    # 1. Preprocess input
    input_tensor, original_bgr, (orig_w, orig_h) = preprocess_image_for_inference(
        image_input=image_input,
        img_size=cfg.img_size,
    )
    input_tensor = input_tensor.to(dev)

    # 2. Load model
    model, ckpt_status = load_segmentation_model(
        checkpoint_path=checkpoint_path,
        config=cfg,
        device=dev,
    )

    # 3. Predict probabilities
    with torch.no_grad():
        if model is not None:
            probs = model.predict_probabilities(input_tensor).squeeze(0).cpu().numpy()  # (C, H, W)
        else:
            probs = np.zeros((cfg.num_classes, cfg.img_size[0], cfg.img_size[1]), dtype=np.float32)

    # 4. Binarize per class using configured thresholds
    binary_masks = np.zeros_like(probs, dtype=np.uint8)
    for c_idx, c_name in enumerate(cfg.classes):
        thresh = cfg.thresholds.get(c_name, 0.5)
        binary_masks[c_idx] = (probs[c_idx] >= thresh).astype(np.uint8)

    # 5. Connected components and morphological lesion counting
    lesion_counts: Dict[str, int] = {}
    per_class_areas: Dict[str, float] = {}
    total_pixels = orig_w * orig_h

    for c_idx, c_name in enumerate(cfg.classes):
        mask_c = binary_masks[c_idx]
        # Connected components count
        num_labels, _ = cv2.connectedComponents(mask_c)
        lesion_counts[c_name] = max(0, num_labels - 1)  # Subtract background label

        # Scaled area fraction
        area_pixels = np.sum(mask_c > 0)
        per_class_areas[c_name] = round(float(area_pixels / (cfg.img_size[0] * cfg.img_size[1])), 6)

    total_lesion_pixels = np.sum(np.max(binary_masks, axis=0) > 0)
    total_area_ratio = round(float(total_lesion_pixels / (cfg.img_size[0] * cfg.img_size[1])), 6)
    lesion_detected = bool(total_lesion_pixels > 0)

    # Confidence calculation: mean probability in detected lesion regions
    if lesion_detected:
        active_probs = probs[binary_masks > 0]
        confidence = round(float(np.mean(active_probs)), 4)
    else:
        # Confidence that image has no lesions
        confidence = round(float(1.0 - np.mean(probs)), 4)

    # 6. Save Artifacts (Overlays and Masks)
    mask_path: Optional[str] = None
    overlay_path: Optional[str] = None

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        img_stem = Path(str(image_input)).stem if isinstance(image_input, (str, Path)) else "sample"

        # Generate and save overlay
        overlay = generate_lesion_overlay(original_bgr, binary_masks, classes=cfg.classes)
        overlay_filename = f"{img_stem}_lesion_overlay.jpg"
        overlay_full_path = os.path.join(output_dir, overlay_filename)
        cv2.imwrite(overlay_full_path, overlay)
        overlay_path = str(overlay_full_path)

        # Save composite mask (combined binary projection)
        composite_mask = (np.max(binary_masks, axis=0) * 255).astype(np.uint8)
        composite_resized = cv2.resize(composite_mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        mask_filename = f"{img_stem}_predicted_mask.png"
        mask_full_path = os.path.join(output_dir, mask_filename)
        cv2.imwrite(mask_full_path, composite_resized)
        mask_path = str(mask_full_path)

    return {
        "mask_path": mask_path,
        "overlay_path": overlay_path,
        "lesion_detected": lesion_detected,
        "lesion_counts": lesion_counts,
        "lesion_area_ratio": total_area_ratio,
        "confidence": confidence,
        "per_class_areas": per_class_areas,
        "classes": list(cfg.classes),
        "checkpoint_status": ckpt_status,
        "status": "SUCCESS",
    }

