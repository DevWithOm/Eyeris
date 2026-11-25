"""Training and validation engine for U-Net lesion segmentation.

Features:
- Epoch training and validation loops with metric tracking.
- Masked loss calculation strictly ignoring unannotated channels.
- Early stopping and model checkpointing based on Validation Mean Dice.
- Safe checkpointing: never overwrites best checkpoint without preserving previous version.
- Learning rate scheduling with ReduceLROnPlateau.
- Full training history logging to JSON and YAML.
- Publication-quality training loss and Dice/IoU curves generation.
- Validation sample prediction visual comparison generation.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from ai_models.segmentation.dataset import create_segmentation_dataloaders
from src.vision.segmentation.config import SegmentationConfig
from src.vision.segmentation.losses import CombinedSegmentationLoss
from src.vision.segmentation.metrics import calculate_segmentation_metrics
from src.vision.segmentation.model import UNet


class EarlyStopping:
    """Early stopping to prevent overfitting on small datasets."""

    def __init__(self, patience: int = 10, min_delta: float = 1e-4) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_score: Optional[float] = None
        self.early_stop = False

    def __call__(self, val_score: float) -> bool:
        if self.best_score is None:
            self.best_score = val_score
            return False

        if val_score < self.best_score + self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        else:
            self.best_score = val_score
            self.counter = 0
            return False
        return False


def train_one_epoch(
    model: UNet,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    criterion: CombinedSegmentationLoss,
    device: str,
) -> Dict[str, float]:
    """Train the model for one epoch."""
    model.train()
    total_loss = 0.0
    total_bce = 0.0
    total_dice_loss = 0.0
    num_batches = 0

    for batch in dataloader:
        images = batch["image"].to(device)
        masks = batch["masks"].to(device)
        mask_valid = batch["mask_valid"].to(device)

        optimizer.zero_grad()
        logits = model(images)

        losses = criterion(logits, masks, mask_valid)
        loss = losses["loss"]

        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        total_bce += losses["bce_loss"].item()
        total_dice_loss += losses["dice_loss"].item()
        num_batches += 1

    return {
        "train_loss": round(total_loss / max(num_batches, 1), 4),
        "train_bce": round(total_bce / max(num_batches, 1), 4),
        "train_dice_loss": round(total_dice_loss / max(num_batches, 1), 4),
    }


@torch.no_grad()
def evaluate_epoch(
    model: UNet,
    dataloader: DataLoader,
    criterion: CombinedSegmentationLoss,
    device: str,
    classes: Sequence[str] = ("MA", "HE", "EX", "SE"),
    threshold: float = 0.5,
) -> Dict[str, float]:
    """Evaluate the model on a validation or test DataLoader."""
    model.eval()
    total_loss = 0.0
    all_logits: List[torch.Tensor] = []
    all_targets: List[torch.Tensor] = []
    all_valids: List[torch.Tensor] = []
    num_batches = 0

    for batch in dataloader:
        images = batch["image"].to(device)
        masks = batch["masks"].to(device)
        mask_valid = batch["mask_valid"].to(device)

        logits = model(images)
        losses = criterion(logits, masks, mask_valid)

        total_loss += losses["loss"].item()
        num_batches += 1

        all_logits.append(logits.cpu())
        all_targets.append(masks.cpu())
        all_valids.append(mask_valid.cpu())

    avg_loss = total_loss / max(num_batches, 1)

    cat_logits = torch.cat(all_logits, dim=0)
    cat_targets = torch.cat(all_targets, dim=0)
    cat_valids = torch.cat(all_valids, dim=0)

    metrics = calculate_segmentation_metrics(
        logits_or_probs=cat_logits,
        targets=cat_targets,
        mask_valid=cat_valids,
        threshold=threshold,
        class_names=classes,
    )
    metrics["val_loss"] = round(avg_loss, 4)
    return metrics


def generate_training_plots(
    history: List[Dict[str, Any]],
    plot_dir: str | Path,
) -> Dict[str, str]:
    """Generates training loss, validation loss, Dice, and IoU metric plots."""
    os.makedirs(plot_dir, exist_ok=True)
    epochs = [h["epoch"] for h in history]
    train_losses = [h["train_loss"] for h in history]
    val_losses = [h["val_loss"] for h in history]
    mean_dices = [h["mean_dice"] for h in history]
    mean_ious = [h["mean_iou"] for h in history]

    # 1. Loss curves (Train vs Val, BCE vs Dice)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot(epochs, train_losses, label="Train Loss (Total)", color="#1f77b4", lw=2, marker="o")
    ax1.plot(epochs, val_losses, label="Val Loss (Total)", color="#ff7f0e", lw=2, marker="s")
    ax1.set_xlabel("Epoch", fontsize=11)
    ax1.set_ylabel("Loss", fontsize=11)
    ax1.set_title("Training and Validation Loss", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend()

    train_bce = [h["train_bce"] for h in history]
    train_dice_loss = [h["train_dice_loss"] for h in history]
    ax2.plot(epochs, train_bce, label="Train BCE Loss", color="#2ca02c", lw=2, linestyle="--")
    ax2.plot(epochs, train_dice_loss, label="Train Soft Dice Loss", color="#d62728", lw=2, linestyle="-.")
    ax2.set_xlabel("Epoch", fontsize=11)
    ax2.set_ylabel("Component Loss", fontsize=11)
    ax2.set_title("Loss Components (BCE vs Soft Dice)", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend()
    plt.tight_layout()
    loss_path = os.path.join(plot_dir, "loss_curves.png")
    fig.savefig(loss_path, dpi=200)
    plt.close(fig)

    # 2. Overall Metrics (Dice and IoU)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(epochs, mean_dices, label="Validation Mean Dice", color="#2ca02c", lw=2.5, marker="o")
    ax.plot(epochs, mean_ious, label="Validation Mean IoU", color="#9467bd", lw=2.5, marker="^")
    ax.set_xlabel("Epoch", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Validation Dice and IoU Progression", fontsize=12, fontweight="bold")
    ax.set_ylim([0.0, 1.0])
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="lower right")
    plt.tight_layout()
    metrics_path = os.path.join(plot_dir, "metrics_curves.png")
    fig.savefig(metrics_path, dpi=200)
    plt.close(fig)

    # 3. Per-Class Dice
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {
        "dice_MA": "#d62728",
        "dice_HE": "#8c564b",
        "dice_EX": "#bcbd22",
        "dice_SE": "#17becf",
    }
    labels = {
        "dice_MA": "Microaneurysms (MA)",
        "dice_HE": "Haemorrhages (HE)",
        "dice_EX": "Hard Exudates (EX)",
        "dice_SE": "Soft Exudates (SE)",
    }
    for k, col in colors.items():
        if k in history[0]:
            vals = [h.get(k, 0.0) for h in history]
            ax.plot(epochs, vals, label=labels[k], color=col, lw=2, marker="x")
    ax.set_xlabel("Epoch", fontsize=11)
    ax.set_ylabel("Dice Score", fontsize=11)
    ax.set_title("Per-Class Lesion Segmentation Dice Score", fontsize=12, fontweight="bold")
    ax.set_ylim([0.0, 1.0])
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left")
    plt.tight_layout()
    per_class_path = os.path.join(plot_dir, "per_class_dice.png")
    fig.savefig(per_class_path, dpi=200)
    plt.close(fig)

    return {
        "loss_curves": loss_path,
        "metrics_curves": metrics_path,
        "per_class_dice": per_class_path,
    }


def generate_sample_comparisons(
    model: UNet,
    val_loader: DataLoader,
    output_dir: str | Path,
    device: str,
    classes: Sequence[str] = ("MA", "HE", "EX", "SE"),
    threshold: float = 0.5,
    num_samples: int = 3,
) -> List[str]:
    """Generates and saves visual comparisons between ground-truth and predictions."""
    os.makedirs(output_dir, exist_ok=True)
    model.eval()
    saved_files: List[str] = []
    samples_collected = 0

    with torch.no_grad():
        for batch in val_loader:
            images = batch["image"].to(device)
            masks = batch["masks"]  # (B, C, H, W)
            mask_valid = batch["mask_valid"]  # (B, C)
            image_ids = batch["image_id"]

            logits = model(images)
            probs = torch.sigmoid(logits).cpu()
            pred_masks = (probs >= threshold).float()

            for b in range(images.size(0)):
                if samples_collected >= num_samples:
                    break
                img_id = image_ids[b]
                # Denormalize image for visualization
                img_np = images[b].cpu().permute(1, 2, 0).numpy()
                mean = np.array([0.485, 0.456, 0.406])
                std = np.array([0.229, 0.224, 0.225])
                img_np = np.clip((img_np * std + mean) * 255.0, 0, 255).astype(np.uint8)

                # Create multi-panel comparison figure
                fig, axes = plt.subplots(4, 4, figsize=(16, 16))
                for c_idx, c_name in enumerate(classes):
                    is_valid = mask_valid[b, c_idx].item()
                    gt_m = masks[b, c_idx].numpy()
                    p_prob = probs[b, c_idx].numpy()
                    p_mask = pred_masks[b, c_idx].numpy()

                    # Col 0: Original Image
                    axes[c_idx, 0].imshow(img_np)
                    if c_idx == 0:
                        axes[c_idx, 0].set_title(f"{img_id} - Fundus Image", fontsize=11, fontweight="bold")
                    axes[c_idx, 0].set_ylabel(c_name, fontsize=12, fontweight="bold")
                    axes[c_idx, 0].axis("off")

                    # Col 1: Ground Truth
                    if is_valid:
                        axes[c_idx, 1].imshow(gt_m, cmap="hot", vmin=0, vmax=1)
                        gt_sum = int(np.sum(gt_m > 0))
                        title = f"GT Mask ({gt_sum} px)" if c_idx == 0 else f"{gt_sum} px"
                        axes[c_idx, 1].set_title(title, fontsize=10)
                    else:
                        axes[c_idx, 1].text(
                            0.5, 0.5, "Not Annotated\nin IDRiD",
                            ha="center", va="center", color="gray", fontsize=10
                        )
                        title = "GT (Unavailable)" if c_idx == 0 else "Unavailable"
                        axes[c_idx, 1].set_title(title, fontsize=10)
                    axes[c_idx, 1].axis("off")

                    # Col 2: Predicted Probability
                    axes[c_idx, 2].imshow(p_prob, cmap="magma", vmin=0, vmax=1)
                    title = f"Pred Prob (max: {p_prob.max():.2f})" if c_idx == 0 else f"max: {p_prob.max():.2f}"
                    axes[c_idx, 2].set_title(title, fontsize=10)
                    axes[c_idx, 2].axis("off")

                    # Col 3: Predicted Binary Mask
                    p_sum = int(np.sum(p_mask > 0))
                    axes[c_idx, 3].imshow(p_mask, cmap="gray", vmin=0, vmax=1)
                    title = f"Pred Mask ({p_sum} px)" if c_idx == 0 else f"{p_sum} px"
                    axes[c_idx, 3].set_title(title, fontsize=10)
                    axes[c_idx, 3].axis("off")

                plt.suptitle(f"Lesion Ground Truth vs Model Prediction: {img_id}", fontsize=14, y=0.99, fontweight="bold")
                plt.tight_layout()
                save_path = os.path.join(output_dir, f"{img_id}_comparison.png")
                fig.savefig(save_path, dpi=200, bbox_inches="tight")
                plt.close(fig)
                saved_files.append(save_path)
                samples_collected += 1

            if samples_collected >= num_samples:
                break

    return saved_files


def train_segmentation_model(
    config: Optional[SegmentationConfig] = None,
    override_epochs: Optional[int] = None,
) -> Dict[str, Any]:
    """Orchestrates model training, validation, early stopping, and checkpointing.

    Args:
        config: Training configuration. Defaults to SegmentationConfig().
        override_epochs: Optional override for number of epochs.

    Returns:
        Dict with best_val_dice, training history, and checkpoint file paths.
    """
    cfg = config or SegmentationConfig()
    epochs = override_epochs or cfg.epochs
    dev = cfg.device

    os.makedirs(cfg.checkpoint_dir, exist_ok=True)
    os.makedirs(cfg.log_dir, exist_ok=True)
    os.makedirs(cfg.plot_dir, exist_ok=True)
    os.makedirs(cfg.prediction_dir, exist_ok=True)

    # Save active config to YAML
    cfg.save_yaml(os.path.join(cfg.log_dir, "training_config.yaml"))

    # 1. Reproducible seed
    torch.manual_seed(cfg.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(cfg.seed)

    # 2. DataLoaders
    if getattr(cfg, "use_patches", False):
        from ai_models.segmentation.dataset import create_patch_dataloaders
        loaders = create_patch_dataloaders(
            patch_dir=cfg.patch_dir,
            batch_size=cfg.batch_size,
            classes=cfg.classes,
        )
    else:
        loaders = create_segmentation_dataloaders(
            root_dir=cfg.dataset_root,
            batch_size=cfg.batch_size,
            val_fraction=cfg.val_fraction,
            seed=cfg.seed,
            img_size=cfg.img_size,
            classes=cfg.classes,
        )
    train_loader = loaders["train"]
    val_loader = loaders["val"]

    # 3. Model, Loss, Optimizer, Scheduler
    model = UNet(
        in_channels=cfg.in_channels,
        num_classes=cfg.num_classes,
        base_channels=cfg.base_channels,
        bilinear=cfg.bilinear,
    ).to(dev)

    criterion = CombinedSegmentationLoss(
        alpha=cfg.alpha_bce,
        beta=cfg.beta_dice,
    )

    optimizer = optim.AdamW(
        model.parameters(),
        lr=cfg.learning_rate,
        weight_decay=cfg.weight_decay,
    )

    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=4,
    )

    early_stopping = EarlyStopping(patience=cfg.early_stopping_patience)

    history: List[Dict[str, Any]] = []
    best_val_dice = -1.0
    best_epoch = 0
    best_ckpt_path = os.path.join(cfg.checkpoint_dir, "best_model.pth")
    prev_ckpt_path = os.path.join(cfg.checkpoint_dir, "best_model_prev.pth")
    latest_ckpt_path = os.path.join(cfg.checkpoint_dir, "latest_checkpoint.pth")

    start_time = time.time()
    print(f"[*] Starting segmentation training on {dev.upper()} for {epochs} epochs...")
    print(f"[*] Training samples: {len(train_loader.dataset)}, Validation samples: {len(val_loader.dataset)}")
    print(f"[*] Image resolution: {cfg.img_size}, Batch size: {cfg.batch_size}, Base channels: {cfg.base_channels}")

    for epoch in range(1, epochs + 1):
        epoch_t0 = time.time()
        train_res = train_one_epoch(model, train_loader, optimizer, criterion, dev)
        val_res = evaluate_epoch(model, val_loader, criterion, dev, classes=cfg.classes)

        val_dice = val_res["mean_dice"]
        val_loss = val_res["val_loss"]
        scheduler.step(val_dice)

        epoch_duration = round(time.time() - epoch_t0, 2)
        epoch_record = {
            "epoch": epoch,
            **train_res,
            **val_res,
            "lr": optimizer.param_groups[0]["lr"],
            "epoch_duration_seconds": epoch_duration,
        }
        history.append(epoch_record)

        print(
            f"Epoch {epoch:02d}/{epochs:02d} [{epoch_duration:.1f}s] - "
            f"Train Loss: {train_res['train_loss']:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Mean Dice: {val_dice:.4f} | "
            f"Val Mean IoU: {val_res['mean_iou']:.4f} | "
            f"MA: {val_res.get('dice_MA', 0.0):.4f}, "
            f"HE: {val_res.get('dice_HE', 0.0):.4f}, "
            f"EX: {val_res.get('dice_EX', 0.0):.4f}, "
            f"SE: {val_res.get('dice_SE', 0.0):.4f}"
        )

        # Save best model with preservation of previous best
        if val_dice > best_val_dice:
            best_val_dice = val_dice
            best_epoch = epoch

            # Preserve previous best checkpoint before overwriting
            if os.path.exists(best_ckpt_path):
                shutil.copy2(best_ckpt_path, prev_ckpt_path)

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_dice": val_dice,
                    "val_metrics": val_res,
                    "config": cfg.to_dict(),
                },
                best_ckpt_path,
            )

            # Also save milestone checkpoint
            milestone_path = os.path.join(
                cfg.checkpoint_dir, f"checkpoint_epoch_{epoch:02d}_dice_{val_dice:.4f}.pth"
            )
            shutil.copy2(best_ckpt_path, milestone_path)
            print(f"    --> [NEW BEST] Checkpoint saved at epoch {epoch:02d} (Val Mean Dice: {val_dice:.4f})")

        # Save latest checkpoint
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "history": history,
            },
            latest_ckpt_path,
        )

        if early_stopping(val_dice):
            print(f"[*] Early stopping triggered after {epoch} epochs.")
            break

    total_duration = round(time.time() - start_time, 2)
    print(f"[*] Training complete in {total_duration}s. Best epoch: {best_epoch} with Val Mean Dice: {best_val_dice:.4f}")

    # 4. Save training history log to JSON
    log_file = os.path.join(cfg.log_dir, "training_history.json")
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_epoch": best_epoch,
                "best_val_dice": best_val_dice,
                "total_epochs_trained": len(history),
                "duration_seconds": total_duration,
                "config": cfg.to_dict(),
                "history": history,
            },
            f,
            indent=2,
        )

    # 5. Generate and save metric plots
    print("[*] Generating training loss, metrics, and per-class plots...")
    plot_files = generate_training_plots(history, cfg.plot_dir)

    # 6. Load best model weights and generate sample predictions
    print("[*] Generating sample validation predictions vs ground truth...")
    best_checkpoint = torch.load(best_ckpt_path, map_location=dev, weights_only=False)
    model.load_state_dict(best_checkpoint["model_state_dict"])
    sample_files = generate_sample_comparisons(
        model=model,
        val_loader=val_loader,
        output_dir=cfg.prediction_dir,
        device=dev,
        classes=cfg.classes,
        threshold=0.5,
        num_samples=3,
    )

    return {
        "best_epoch": best_epoch,
        "best_val_dice": best_val_dice,
        "epochs_trained": len(history),
        "duration_seconds": total_duration,
        "best_checkpoint": best_ckpt_path,
        "prev_checkpoint": prev_ckpt_path if os.path.exists(prev_ckpt_path) else None,
        "log_file": log_file,
        "plot_files": plot_files,
        "sample_files": sample_files,
        "history": history,
    }
