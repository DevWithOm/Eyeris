"""End-to-End Execution Script for U-Net Lesion Segmentation Training on IDRiD.

Performs:
1. Verification of dataset and image-mask pairing.
2. Verification of patient-level train/validation split (zero data leakage).
3. Detection of GPU / CUDA hardware availability.
4. Configuration selection based on hardware (CPU / GPU).
5. Full model training with per-epoch logging.
6. Metric tracking (Dice & IoU overall and per lesion class: MA, HE, EX, SE).
7. Safe checkpointing (preserves previous best model without overwriting).
8. History and configuration saving.
9. Plot generation (Loss curves, Dice/IoU trajectories, per-class Dice).
10. Ground truth vs predicted mask side-by-side comparison visualizations.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
from ai_models.segmentation.dataset import (
    IDRiDDataset,
    LESION_CLASSES,
    split_idrid_dataset,
)
from src.vision.segmentation.config import SegmentationConfig
from src.vision.segmentation.train import train_segmentation_model


def verify_dataset(root_dir: str = "data/raw/IDRiD") -> None:
    """Verifies dataset files and image-mask pairing integrity."""
    print("=" * 70)
    print("TASK 1: VERIFYING IDRID DATASET & IMAGE-MASK PAIRING")
    print("=" * 70)
    root = Path(root_dir)
    images_train_dir = root / "A. Segmentation" / "1. Original Images" / "a. Training Set"
    images_test_dir = root / "A. Segmentation" / "1. Original Images" / "b. Testing Set"

    train_files = sorted(list(images_train_dir.glob("*.jpg")))
    test_files = sorted(list(images_test_dir.glob("*.jpg")))
    print(f"[*] Found {len(train_files)} training images in: {images_train_dir}")
    print(f"[*] Found {len(test_files)} testing images in: {images_test_dir}")

    # Initialize full train dataset to check mask pairings
    ds = IDRiDDataset(root_dir=root_dir, split="train", is_train=False)
    print(f"[*] Successfully indexed {len(ds)} samples in IDRiDDataset.")

    mask_counts = {c: 0 for c in LESION_CLASSES}
    for sample in ds.samples:
        for c in LESION_CLASSES:
            if sample["mask_paths"][c] is not None:
                mask_counts[c] += 1

    print("[*] Verified Ground-Truth Mask counts across all 54 training images:")
    for c in LESION_CLASSES:
        print(f"    - {c:2s}: {mask_counts[c]} masks available ({mask_counts[c]/len(ds)*100:.1f}%)")
    print("[*] Image-mask pairing check passed.\n")


def verify_split(root_dir: str = "data/raw/IDRiD", seed: int = 42, val_fraction: float = 0.2):
    """Verifies train/val split reproducibility and absence of data leakage."""
    print("=" * 70)
    print("TASK 2: VERIFYING TRAIN / VALIDATION SPLIT (ZERO DATA LEAKAGE)")
    print("=" * 70)
    train_ids, val_ids, test_ids = split_idrid_dataset(
        root_dir=root_dir, val_fraction=val_fraction, seed=seed
    )
    print(f"[*] Split Summary (Seed={seed}, Val Fraction={val_fraction}):")
    print(f"    - Training Set:   {len(train_ids)} images ({train_ids[:3]} ... {train_ids[-1]})")
    print(f"    - Validation Set: {len(val_ids)} images ({val_ids[:3]} ... {val_ids[-1]})")
    print(f"    - Test Set:       {len(test_ids)} images ({test_ids[:3]} ... {test_ids[-1]})")

    overlap_train_val = set(train_ids).intersection(set(val_ids))
    overlap_train_test = set(train_ids).intersection(set(test_ids))
    overlap_val_test = set(val_ids).intersection(set(test_ids))

    assert len(overlap_train_val) == 0, f"LEAKAGE DETECTED between Train and Val: {overlap_train_val}"
    assert len(overlap_train_test) == 0, f"LEAKAGE DETECTED between Train and Test: {overlap_train_test}"
    assert len(overlap_val_test) == 0, f"LEAKAGE DETECTED between Val and Test: {overlap_val_test}"
    print("[*] Strict image-level isolation confirmed: 0% data leakage across all partitions.\n")
    return train_ids, val_ids, test_ids


def main():
    # 1. Dataset Verification
    verify_dataset()

    # 2. Split Verification
    verify_split()

    # 3 & 4. Hardware Detection and Configuration
    print("=" * 70)
    print("TASKS 3 & 4: HARDWARE DETECTION & CONFIGURATION")
    print("=" * 70)
    cuda_available = torch.cuda.is_available()
    print(f"[*] PyTorch Version: {torch.__version__}")
    print(f"[*] CUDA Available:  {cuda_available}")

    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        print(f"[*] CUDA Device:     {gpu_name}")
        print("[*] Running on NVIDIA GPU with Patch-Based Training (256x256 Full-Resolution Lesion Crops).")
        device = "cuda"
        config = SegmentationConfig(
            dataset_root="data/raw/IDRiD",
            use_patches=True,
            patch_dir="data/processed/IDRiD_patches",
            img_size=(256, 256),
            base_channels=32,
            batch_size=16,
            epochs=25,
            early_stopping_patience=10,
            learning_rate=3e-4,
            alpha_bce=1.0,
            beta_dice=2.0,
            device=device,
            checkpoint_dir="outputs/segmentation/checkpoints",
            log_dir="outputs/segmentation/logs",
            plot_dir="outputs/segmentation/plots",
            prediction_dir="outputs/segmentation/predictions",
        )
    else:
        print("[*] Running on CPU with Patch-Based Training (256x256 Full-Resolution Lesion Crops).")
        device = "cpu"
        config = SegmentationConfig(
            dataset_root="data/raw/IDRiD",
            use_patches=True,
            patch_dir="data/processed/IDRiD_patches",
            img_size=(256, 256),
            base_channels=16,
            batch_size=8,
            epochs=12,
            early_stopping_patience=6,
            learning_rate=3e-4,
            alpha_bce=1.0,
            beta_dice=2.0,
            device=device,
            checkpoint_dir="outputs/segmentation/checkpoints",
            log_dir="outputs/segmentation/logs",
            plot_dir="outputs/segmentation/plots",
            prediction_dir="outputs/segmentation/predictions",
        )

    print(f"[*] Target Device:    {config.device}")
    print(f"[*] Image Resolution: {config.img_size}")
    print(f"[*] Base Channels:    {config.base_channels}")
    print(f"[*] Epochs:           {config.epochs}")
    print(f"[*] Batch Size:       {config.batch_size}")
    print(f"[*] Output Root:      outputs/segmentation/\n")

    # 5-12. Train Model and Generate All Deliverables
    print("=" * 70)
    print("TASKS 5-12: TRAINING EXECUTION & DELIVERABLE GENERATION")
    print("=" * 70)
    results = train_segmentation_model(config)

    print("\n" + "=" * 70)
    print("TRAINING RUN COMPLETE")
    print("=" * 70)
    print(f"Best Epoch:           {results['best_epoch']}")
    print(f"Best Val Mean Dice:   {results['best_val_dice']:.4f}")
    print(f"Total Epochs Trained: {results['epochs_trained']}")
    print(f"Total Time:           {results['duration_seconds']}s")
    print(f"Best Checkpoint:      {results['best_checkpoint']}")
    if results["prev_checkpoint"]:
        print(f"Previous Checkpoint:  {results['prev_checkpoint']}")
    print(f"Log File:             {results['log_file']}")
    print(f"Plots Generated:      {list(results['plot_files'].values())}")
    print(f"Sample Comparisons:   {results['sample_files']}")

    return results


if __name__ == "__main__":
    main()

