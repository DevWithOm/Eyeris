"""U-Net Architecture for Retinal Lesion Segmentation.

Multi-channel / multi-label U-Net architecture predicting 4 independent
lesion probabilities (MA, HE, EX, SE) using Sigmoid activations to support
co-occurring and overlapping pathological retinal features.
"""

from __future__ import annotations

from typing import List, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    """(Convolution => [BatchNorm] => ReLU) * 2"""

    def __init__(self, in_channels: int, out_channels: int, mid_channels: int | None = None) -> None:
        super().__init__()
        if not mid_channels:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.double_conv(x)


class Down(nn.Module):
    """Downscaling with MaxPool then DoubleConv."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.maxpool_conv(x)


class Up(nn.Module):
    """Upscaling with Bilinear/Transposed Conv then DoubleConv with skip connection."""

    def __init__(self, in_channels: int, out_channels: int, bilinear: bool = True) -> None:
        super().__init__()
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        x1 = self.up(x1)
        # Pad x1 if dimensions differ slightly due to odd resolutions
        diff_y = x2.size()[2] - x1.size()[2]
        diff_x = x2.size()[3] - x1.size()[3]

        if diff_x > 0 or diff_y > 0:
            x1 = F.pad(
                x1,
                [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2],
            )
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class UNet(nn.Module):
    """Multi-channel U-Net for retinal lesion segmentation.

    Args:
        in_channels: Number of input channels (3 for RGB fundus image).
        num_classes: Number of lesion classes (4 for MA, HE, EX, SE).
        base_channels: Channel width of the first encoder stage (default 32 for memory efficiency).
        bilinear: If True, uses bilinear upsampling instead of transposed convolution.
    """

    def __init__(
        self,
        in_channels: int = 3,
        num_classes: int = 4,
        base_channels: int = 32,
        bilinear: bool = True,
    ) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.num_classes = num_classes
        self.base_channels = base_channels
        self.bilinear = bilinear

        b = base_channels
        self.inc = DoubleConv(in_channels, b)
        self.down1 = Down(b, b * 2)
        self.down2 = Down(b * 2, b * 4)
        self.down3 = Down(b * 4, b * 8)
        factor = 2 if bilinear else 1
        self.down4 = Down(b * 8, (b * 16) // factor)

        self.up1 = Up(b * 16, (b * 8) // factor, bilinear)
        self.up2 = Up(b * 8, (b * 4) // factor, bilinear)
        self.up3 = Up(b * 4, (b * 2) // factor, bilinear)
        self.up4 = Up(b * 2, b, bilinear)

        # 1x1 conv projecting to num_classes logits
        self.outc = nn.Conv2d(b, num_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning raw logits of shape (B, num_classes, H, W)."""
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        logits = self.outc(x)
        return logits

    @torch.no_grad()
    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass applying independent Sigmoid activation."""
        logits = self.forward(x)
        return torch.sigmoid(logits)

    @torch.no_grad()
    def predict_masks(self, x: torch.Tensor, threshold: float = 0.5) -> torch.Tensor:
        """Forward pass returning binary masks {0.0, 1.0}."""
        probs = self.predict_probabilities(x)
        return (probs >= threshold).float()

