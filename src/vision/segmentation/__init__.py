"""Retinal lesion segmentation subpackage."""

from src.vision.segmentation.config import SegmentationConfig
from src.vision.segmentation.losses import (
    CombinedSegmentationLoss,
    MaskedBCELoss,
    SoftDiceLoss,
)
from src.vision.segmentation.metrics import calculate_segmentation_metrics
from src.vision.segmentation.model import UNet
from src.vision.segmentation.predict import (
    generate_lesion_overlay,
    load_segmentation_model,
    segment_lesions,
)
from src.vision.segmentation.train import (
    EarlyStopping,
    evaluate_epoch,
    train_one_epoch,
    train_segmentation_model,
)

__all__ = [
    "UNet",
    "SegmentationConfig",
    "SoftDiceLoss",
    "MaskedBCELoss",
    "CombinedSegmentationLoss",
    "calculate_segmentation_metrics",
    "segment_lesions",
    "generate_lesion_overlay",
    "load_segmentation_model",
    "train_segmentation_model",
    "train_one_epoch",
    "evaluate_epoch",
    "EarlyStopping",
]

