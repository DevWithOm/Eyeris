"""
Training loop and validation-based checkpointing for EfficientNet-B0 DR classification.
"""

import argparse
from pathlib import Path
import time
from typing import Dict, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.evaluate import evaluate_model


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> Tuple[float, float]:
    """
    Trains model for one epoch over the training DataLoader.
    Returns: (epoch_loss, epoch_accuracy).
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels, _ in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = torch.argmax(outputs, dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    epoch_loss = running_loss / total if total > 0 else 0.0
    epoch_acc = correct / total if total > 0 else 0.0
    return epoch_loss, epoch_acc


def fit_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    device: torch.device = torch.device("cpu"),
    num_epochs: int = 10,
    checkpoint_dir: Optional[Union[str, Path]] = None,
    config: Optional[Dict] = None
) -> Tuple[Dict, float]:
    """
    Executes the training loop with validation checkpoint selection.
    Tracks Loss, Accuracy, and Validation Macro F1.
    Saves best_model.pth when validation Macro F1 achieves a new maximum.
    """
    if checkpoint_dir is not None:
        ckpt_path = Path(checkpoint_dir)
        ckpt_path.mkdir(parents=True, exist_ok=True)
        best_model_path = ckpt_path / "best_model.pth"
        best_ckpt_path = ckpt_path / "best_checkpoint.tar"
        last_model_path = ckpt_path / "last_model.pth"
    else:
        best_model_path = best_ckpt_path = last_model_path = None

    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
        "val_macro_f1": [],
        "lr": []
    }

    best_val_macro_f1 = -1.0
    start_time = time.time()

    print("=" * 82)
    print(f"{'Epoch':^6} | {'Train Loss':^10} | {'Train Acc':^10} | {'Val Loss':^10} | {'Val Acc':^10} | {'Val Macro F1':^12} | {'Time':^8}")
    print("=" * 82)

    for epoch in range(1, num_epochs + 1):
        epoch_start = time.time()

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_f1, _, _, _ = evaluate_model(model, val_loader, criterion, device)

        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["val_macro_f1"].append(val_f1)
        history["lr"].append(current_lr)

        if scheduler is not None:
            if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                scheduler.step(val_f1)
            else:
                scheduler.step()

        epoch_time = time.time() - epoch_start
        print(f"{epoch:^6d} | {train_loss:^10.4f} | {train_acc * 100:^9.2f}% | {val_loss:^10.4f} | {val_acc * 100:^9.2f}% | {val_f1:^12.4f} | {epoch_time:^7.1f}s", end="")

        if val_f1 > best_val_macro_f1:
            best_val_macro_f1 = val_f1
            if best_model_path is not None:
                torch.save(model.state_dict(), best_model_path)
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_macro_f1": val_f1,
                    "val_loss": val_loss,
                    "config": config
                }, best_ckpt_path)
            print(f"  🌟 [BEST CHECKPOINT SAVED: F1={val_f1:.4f}]")
        else:
            print("")

    if last_model_path is not None:
        torch.save(model.state_dict(), last_model_path)

    total_time = time.time() - start_time
    print("=" * 82)
    print(f"Training completed in {total_time / 60:.2f} minutes.")
    print(f"Best Validation Macro F1: {best_val_macro_f1:.4f}")
    if best_model_path is not None:
        print(f"Saved best weights: {best_model_path}")

    return history, best_val_macro_f1
