"""Training entry point for U-Net lesion segmentation."""

from src.vision.segmentation.train import (
    EarlyStopping,
    evaluate_epoch,
    train_one_epoch,
    train_segmentation_model,
)

__all__ = [
    "train_segmentation_model",
    "train_one_epoch",
    "evaluate_epoch",
    "EarlyStopping",
]
