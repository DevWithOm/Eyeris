"""
Diabetic Retinopathy Grade Prediction (Inference).

Implements the contract-compliant predict_grade(image_path: str) -> dict
using the cached EfficientNet-B0 classifier.
"""

from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np
import torch
import torch.nn as nn

from ai_models.classification.model import DEFAULT_CHECKPOINT_PATH, get_classification_model
from ai_models.classification.preprocessing import preprocess_fundus_image
from ai_models.common.labels import DR_GRADE_LABELS

MODEL_NAME = "efficientnet_b0"
MODEL_VERSION = "1.0.0"

# Module-level cache to ensure weights are loaded only once across screening requests
_CACHED_MODEL: Optional[nn.Module] = None
_CACHED_DEVICE: Optional[torch.device] = None
_CACHED_CHECKPOINT: Optional[Path] = None


def get_cached_model(
    checkpoint_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
    force_reload: bool = False,
) -> nn.Module:
    """
    Returns the cached classification model instance.
    Loads and caches weights if not already loaded, or if force_reload=True.

    Exposes the loaded model instance for downstream explainability (e.g. Grad-CAM)
    without redundant memory allocations.
    """
    global _CACHED_MODEL, _CACHED_DEVICE, _CACHED_CHECKPOINT

    target_checkpoint = Path(checkpoint_path) if checkpoint_path else DEFAULT_CHECKPOINT_PATH
    if device is None:
        target_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif isinstance(device, str):
        target_device = torch.device(device)
    else:
        target_device = device

    if (
        _CACHED_MODEL is None
        or force_reload
        or _CACHED_DEVICE != target_device
        or _CACHED_CHECKPOINT != target_checkpoint
    ):
        _CACHED_MODEL = get_classification_model(
            checkpoint_path=target_checkpoint,
            device=target_device,
        )
        _CACHED_DEVICE = target_device
        _CACHED_CHECKPOINT = target_checkpoint

    return _CACHED_MODEL


def predict_grade(
    image_path: str,
    checkpoint_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> Dict[str, Union[int, str, float, list]]:
    """
    Evaluates a single retinal fundus image and returns DR classification results.

    Adheres strictly to docs/integration_contract.md:
        predict_grade(image_path: str) -> dict

    Clinical policy note:
        Clinical referral decisions (e.g. referable DR thresholding) are decoupled
        and delegated to integration/decision_engine.py.
    
    Calibration note:
        'raw_confidence' is the uncalibrated maximum softmax output. Calibrated
        probabilities and uncertainty estimation are handled in ai_models/explainability/.

    Args:
        image_path: Path to the retinal fundus image file.
        checkpoint_path: Optional custom path to model weights (defaults to artifacts/model_weights/best_model.pth).
        device: Target device ('cpu', 'cuda', or None for auto-detection).

    Returns:
        dict:
            predicted_grade (int): DR grade from 0 to 4.
            grade_name (str): Clinical grade label (e.g. "Moderate").
            probabilities (list[float]): Softmax probabilities for grades [0, 1, 2, 3, 4].
            raw_confidence (float): Uncalibrated max softmax probability.
            confidence (float): Alias for raw_confidence for pipeline compatibility.
            model_name (str): "efficientnet_b0".
            model_version (str): "1.0.0".
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    # Determine execution device
    if device is None:
        target_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif isinstance(device, str):
        target_device = torch.device(device)
    else:
        target_device = device

    model = get_cached_model(checkpoint_path=checkpoint_path, device=target_device)

    # Preprocess image (RGB conversion, border crop, resize 224x224, ImageNet normalization)
    tensor = preprocess_fundus_image(path, image_size=224, crop_borders=True)
    tensor = tensor.to(target_device)

    # Execute inference
    model.eval()
    with torch.no_grad():
        logits = model(tensor)
        probs_tensor = torch.softmax(logits, dim=1)
        probs = probs_tensor.cpu().numpy()[0]

    pred_grade = int(np.argmax(probs))
    raw_confidence = float(probs[pred_grade])
    grade_name = DR_GRADE_LABELS.get(pred_grade, f"Grade {pred_grade}")

    return {
        "predicted_grade": pred_grade,
        "grade_name": grade_name,
        "probabilities": [float(p) for p in probs],
        "raw_confidence": raw_confidence,
        "confidence": raw_confidence,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
    }
