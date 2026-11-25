"""Configuration dataclass and YAML loader for U-Net lesion segmentation."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Tuple
import yaml
import torch


@dataclass
class SegmentationConfig:
    """Configurable training and inference hyperparameters."""

    # Data
    dataset_root: str = "data/raw/IDRiD"
    val_fraction: float = 0.2
    seed: int = 42
    img_size: Tuple[int, int] = (256, 256)
    classes: Tuple[str, ...] = ("MA", "HE", "EX", "SE")
    use_patches: bool = False
    patch_dir: str = "data/processed/IDRiD_patches"

    # Architecture
    in_channels: int = 3
    num_classes: int = 4
    base_channels: int = 16
    bilinear: bool = True

    # Training
    batch_size: int = 4
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    epochs: int = 15
    early_stopping_patience: int = 6
    alpha_bce: float = 1.0
    beta_dice: float = 1.0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

    # Paths
    checkpoint_dir: str = "outputs/segmentation/checkpoints"
    log_dir: str = "outputs/segmentation/logs"
    plot_dir: str = "outputs/segmentation/plots"
    prediction_dir: str = "outputs/segmentation/predictions"

    # Inference thresholds per lesion class
    thresholds: Dict[str, float] = field(
        default_factory=lambda: {"MA": 0.5, "HE": 0.5, "EX": 0.5, "SE": 0.5}
    )

    def to_dict(self) -> Dict:
        """Convert config to dictionary with YAML-safe types."""
        d = asdict(self)
        d["classes"] = list(d["classes"])
        d["img_size"] = list(d["img_size"])
        return d

    def save_yaml(self, path: str | Path) -> None:
        """Save configuration to YAML file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    @classmethod
    def from_yaml(cls, path: str | Path) -> SegmentationConfig:
        """Load configuration from YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Convert list back to tuple if needed
        if "img_size" in data and isinstance(data["img_size"], list):
            data["img_size"] = tuple(data["img_size"])
        if "classes" in data and isinstance(data["classes"], list):
            data["classes"] = tuple(data["classes"])
        return cls(**data)
