"""Evaluation metrics for multi-channel retinal lesion segmentation.

Provides:
- Per-class Dice Coefficient
- Per-class Jaccard Index (IoU)
- Per-class Precision & Recall
- Mean Dice and Mean IoU across all valid lesion categories
"""

from __future__ import annotations

from typing import Dict, Sequence, Tuple
import torch


@torch.no_grad()
def calculate_segmentation_metrics(
    logits_or_probs: torch.Tensor,
    targets: torch.Tensor,
    mask_valid: torch.Tensor,
    threshold: float = 0.5,
    class_names: Sequence[str] = ("MA", "HE", "EX", "SE"),
    eps: float = 1e-7,
) -> Dict[str, float]:
    """Compute per-class and mean Dice and IoU metrics strictly over valid annotations.

    Args:
        logits_or_probs: Tensor of shape (B, C, H, W). If values outside [0, 1], sigmoid is applied.
        targets: Binary ground truth of shape (B, C, H, W) in {0.0, 1.0}.
        mask_valid: BoolTensor of shape (B, C) indicating presence of ground truth.
        threshold: Decision threshold for binarizing probabilities.
        class_names: Names for each of the C channels.
        eps: Small epsilon for numerical stability.

    Returns:
        Dict containing per-class dice, per-class iou, mean_dice, and mean_iou.
    """
    if logits_or_probs.min() < 0.0 or logits_or_probs.max() > 1.0:
        probs = torch.sigmoid(logits_or_probs)
    else:
        probs = logits_or_probs

    preds_binary = (probs >= threshold).float()
    targets_binary = (targets >= 0.5).float()

    b, c = preds_binary.shape[:2]
    preds_flat = preds_binary.view(b, c, -1)
    targets_flat = targets_binary.view(b, c, -1)

    metrics: Dict[str, float] = {}
    valid_class_dices: list[float] = []
    valid_class_ious: list[float] = []

    for c_idx, name in enumerate(class_names):
        # Filter samples where this class has an annotation
        valid_samples = mask_valid[:, c_idx]
        if not valid_samples.any():
            metrics[f"dice_{name}"] = 0.0
            metrics[f"iou_{name}"] = 0.0
            continue

        p_valid = preds_flat[valid_samples, c_idx]  # (N_valid, H*W)
        t_valid = targets_flat[valid_samples, c_idx]

        intersection = (p_valid * t_valid).sum().item()
        total_p = p_valid.sum().item()
        total_t = t_valid.sum().item()
        union = total_p + total_t - intersection

        # Dice = 2 * |P ∩ T| / (|P| + |T|)
        dice = (2.0 * intersection + eps) / (total_p + total_t + eps)
        # IoU = |P ∩ T| / |P ∪ T|
        iou = (intersection + eps) / (union + eps)

        precision = (intersection + eps) / (total_p + eps)
        recall = (intersection + eps) / (total_t + eps)

        metrics[f"dice_{name}"] = round(dice, 4)
        metrics[f"iou_{name}"] = round(iou, 4)
        metrics[f"precision_{name}"] = round(precision, 4)
        metrics[f"recall_{name}"] = round(recall, 4)

        valid_class_dices.append(dice)
        valid_class_ious.append(iou)

    metrics["mean_dice"] = round(sum(valid_class_dices) / max(len(valid_class_dices), 1), 4)
    metrics["mean_iou"] = round(sum(valid_class_ious) / max(len(valid_class_ious), 1), 4)

    return metrics

