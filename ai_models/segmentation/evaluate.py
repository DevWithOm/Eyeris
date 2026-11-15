"""Evaluation metrics and routines for lesion segmentation models."""

from src.vision.segmentation.metrics import calculate_segmentation_metrics
from src.vision.segmentation.train import evaluate_epoch

__all__ = ["calculate_segmentation_metrics", "evaluate_epoch"]
