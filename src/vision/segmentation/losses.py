"""Loss functions for retinal lesion segmentation with missing annotation masking.

CRITICAL DATA RULE:
Never treat an unavailable annotation as a negative mask.
When `mask_valid[b, c] == False`, that channel on that sample is masked out
of both the Binary Cross-Entropy and Dice loss calculations.
"""

from __future__ import annotations

from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class SoftDiceLoss(nn.Module):
    """Soft Dice Loss for multi-channel binary segmentation with missing-annotation masking.

    Formula:
        Dice = (2 * sum(p * y) + smooth) / (sum(p) + sum(y) + smooth)
        Loss = 1 - Dice
    """

    def __init__(self, smooth: float = 1.0, eps: float = 1e-7) -> None:
        super().__init__()
        self.smooth = smooth
        self.eps = eps

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        mask_valid: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Compute soft dice loss.

        Args:
            logits: Predicted logits of shape (B, C, H, W).
            targets: Binary ground truth of shape (B, C, H, W) in {0.0, 1.0}.
            mask_valid: Boolean or float tensor of shape (B, C), where True indicates
                        a valid ground-truth annotation was provided.

        Returns:
            Scalar loss tensor.
        """
        probs = torch.sigmoid(logits)  # (B, C, H, W)

        # Flatten spatial dimensions: (B, C, H*W)
        b, c = probs.shape[:2]
        probs_flat = probs.view(b, c, -1)
        targets_flat = targets.view(b, c, -1)

        intersection = (probs_flat * targets_flat).sum(dim=-1)  # (B, C)
        cardinality = probs_flat.sum(dim=-1) + targets_flat.sum(dim=-1)  # (B, C)

        dice_per_sample_class = (2.0 * intersection + self.smooth) / (cardinality + self.smooth + self.eps)
        loss_per_sample_class = 1.0 - dice_per_sample_class  # (B, C)

        if mask_valid is not None:
            valid_weight = mask_valid.float()  # (B, C)
            valid_count = valid_weight.sum().clamp(min=1.0)
            return (loss_per_sample_class * valid_weight).sum() / valid_count

        return loss_per_sample_class.mean()


class MaskedBCELoss(nn.Module):
    """Binary Cross Entropy Loss with missing annotation masking.

    Ensures that missing lesion masks (e.g. absent HE or SE annotations) do not
    penalize predictions by falsely assuming the region is negative.
    """

    def __init__(self, pos_weight: Optional[torch.Tensor] = None) -> None:
        super().__init__()
        self.pos_weight = pos_weight

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        mask_valid: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Compute masked BCE loss.

        Args:
            logits: (B, C, H, W)
            targets: (B, C, H, W)
            mask_valid: (B, C)
        """
        # Unreduced pixelwise BCE loss
        bce_raw = F.binary_cross_entropy_with_logits(
            logits,
            targets,
            pos_weight=self.pos_weight,
            reduction="none",
        )  # (B, C, H, W)

        # Average over spatial dimensions: (B, C)
        bce_per_sample_class = bce_raw.mean(dim=(-2, -1))

        if mask_valid is not None:
            valid_weight = mask_valid.float()  # (B, C)
            valid_count = valid_weight.sum().clamp(min=1.0)
            return (bce_per_sample_class * valid_weight).sum() / valid_count

        return bce_per_sample_class.mean()


class CombinedSegmentationLoss(nn.Module):
    """Composite Loss = alpha * BCE + beta * SoftDiceLoss.

    Counteracts extreme foreground-background class imbalance while strictly
    masking unannotated channels.
    """

    def __init__(
        self,
        alpha: float = 1.0,
        beta: float = 1.0,
        smooth: float = 1.0,
        pos_weight: Optional[torch.Tensor] = None,
    ) -> None:
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.bce_fn = MaskedBCELoss(pos_weight=pos_weight)
        self.dice_fn = SoftDiceLoss(smooth=smooth)

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        mask_valid: Optional[torch.Tensor] = None,
    ) -> dict[str, torch.Tensor]:
        """Compute total composite loss and individual components."""
        bce_loss = self.bce_fn(logits, targets, mask_valid)
        dice_loss = self.dice_fn(logits, targets, mask_valid)
        total_loss = (self.alpha * bce_loss) + (self.beta * dice_loss)

        return {
            "loss": total_loss,
            "bce_loss": bce_loss,
            "dice_loss": dice_loss,
        }

