"""
Model architecture helpers for five-class Diabetic Retinopathy classification.
Implements pretrained EfficientNet-B0 with custom classification head and loss configuration.
"""

from typing import Optional
import torch
import torch.nn as nn
from torchvision import models


def build_efficientnet_b0(
    num_classes: int = 5,
    pretrained: bool = True,
    dropout: float = 0.3
) -> nn.Module:
    """
    Builds an EfficientNet-B0 model adapted for 5-grade DR classification.
    Initializes from ImageNet pretrained weights and attaches a customized
    dropout + linear classification head.
    """
    try:
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=dropout, inplace=True),
            nn.Linear(in_features=in_features, out_features=num_classes)
        )
    except Exception as e:
        # Fallback to timm if torchvision fails to load or download weights
        try:
            import timm
            model = timm.create_model(
                "efficientnet_b0",
                pretrained=pretrained,
                num_classes=num_classes,
                drop_rate=dropout
            )
        except Exception as timm_err:
            raise RuntimeError(
                f"Failed to build EfficientNet-B0 via torchvision ({e}) and timm ({timm_err})"
            )

    return model


def get_loss_criterion(
    class_weights: Optional[torch.Tensor] = None,
    label_smoothing: float = 0.0
) -> nn.CrossEntropyLoss:
    """
    Returns CrossEntropyLoss configured with optional class weights and label smoothing.
    """
    return nn.CrossEntropyLoss(weight=class_weights, label_smoothing=label_smoothing)
