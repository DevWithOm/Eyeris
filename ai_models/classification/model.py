"""
Diabetic Retinopathy (DR) Classification Model Architecture.

Implements the 5-class EfficientNet-B0 convolutional neural network
adapted for retinal fundus grading (APTOS 2019 / ICDR severity scale).
"""

from pathlib import Path
from typing import Optional, Union

import torch
import torch.nn as nn
from torchvision import models

# Default checkpoint path in project artifacts directory
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKPOINT_PATH = _PROJECT_ROOT / "artifacts" / "model_weights" / "best_model.pth"
_LOCAL_FALLBACK_CHECKPOINT_PATH = Path(__file__).resolve().parent / "best_model.pth"


def build_efficientnet_b0(
    num_classes: int = 5,
    dropout: float = 0.3,
) -> nn.Module:
    """
    Builds the exact torchvision EfficientNet-B0 architecture for 5-class DR classification.

    Head composition:
        Dropout(p=0.3, inplace=True)
        Linear(in_features=1280, out_features=5)

    Matches the saved state dictionary layout:
        features.* (EfficientNet-B0 feature extractor)
        classifier.0 (Dropout)
        classifier.1 (Linear: [5, 1280])
    """
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features  # 1280 for EfficientNet-B0
    model.classifier = nn.Sequential(
        nn.Dropout(p=dropout, inplace=True),
        nn.Linear(in_features=in_features, out_features=num_classes),
    )
    return model


def get_classification_model(
    checkpoint_path: Optional[Union[str, Path]] = None,
    device: Optional[Union[str, torch.device]] = None,
) -> nn.Module:
    """
    Instantiates the EfficientNet-B0 model and loads weights with strict=True.

    Args:
        checkpoint_path: Path to the saved .pth state dict. If None, resolves to
                         artifacts/model_weights/best_model.pth.
        device: Target torch device ('cpu', 'cuda', or torch.device). Auto-detected if None.

    Returns:
        nn.Module: Model in eval mode on target device, ready for inference.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif isinstance(device, str):
        device = torch.device(device)

    # Resolve checkpoint path
    if checkpoint_path is None:
        if DEFAULT_CHECKPOINT_PATH.exists():
            resolved_path = DEFAULT_CHECKPOINT_PATH
        elif _LOCAL_FALLBACK_CHECKPOINT_PATH.exists():
            resolved_path = _LOCAL_FALLBACK_CHECKPOINT_PATH
        else:
            raise FileNotFoundError(
                f"Model checkpoint not found at {DEFAULT_CHECKPOINT_PATH} or {_LOCAL_FALLBACK_CHECKPOINT_PATH}"
            )
    else:
        resolved_path = Path(checkpoint_path)
        if not resolved_path.exists():
            raise FileNotFoundError(f"Specified checkpoint not found: {resolved_path}")

    model = build_efficientnet_b0(num_classes=5, dropout=0.3)
    state_dict = torch.load(resolved_path, map_location=device)

    # Enforce strict loading to guarantee exact architectural match
    model.load_state_dict(state_dict, strict=True)
    model.to(device)
    model.eval()

    return model


def get_gradcam_target_layer(model: nn.Module) -> nn.Module:
    """
    Returns the target convolutional layer for explainability (Grad-CAM).

    For torchvision EfficientNet-B0, this is the last convolutional stage
    (features[-1], Conv2dNormActivation outputting 1280 feature maps).
    """
    if not hasattr(model, "features"):
        raise ValueError("Model does not possess standard torchvision 'features' attribute.")
    return model.features[-1]
