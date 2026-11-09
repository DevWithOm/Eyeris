"""
Diabetic Retinopathy Evaluation and Clinical Metric Computations.
Computes:
  - Multi-class metrics: Per-grade Precision, Recall, F1, Support; Macro F1; Accuracy.
  - Confusion matrix (5x5).
  - Clinical Referable DR metrics: Grades 0-1 (Negative) vs Grades 2-4 (Positive).
    Diagnostic Sensitivity, Specificity, PPV (Precision), NPV, F1, Accuracy.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
try:
    import seaborn as sns
except ImportError:
    sns = None

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

CLASS_NAMES_DEFAULT = [
    "0 - No DR",
    "1 - Mild",
    "2 - Moderate",
    "3 - Severe",
    "4 - Proliferative DR"
]

CLASS_NAMES_SHORT = ["No DR", "Mild", "Moderate", "Severe", "Proliferative"]


def compute_comprehensive_metrics(
    y_true: Union[np.ndarray, List[int]],
    y_pred: Union[np.ndarray, List[int]],
    y_probs: Optional[Union[np.ndarray, List[List[float]]]] = None,
    class_names: Optional[List[str]] = None,
    referable_threshold: int = 2
) -> Dict:
    """
    Computes complete 5-class evaluation metrics and binary Referable DR clinical metrics.
    """
    y_true = np.array(y_true, dtype=int)
    y_pred = np.array(y_pred, dtype=int)

    if class_names is None:
        class_names = CLASS_NAMES_DEFAULT

    # Multi-class metrics
    overall_acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    macro_prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))

    # Per-class classification report
    cls_report = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )

    # 5-class confusion matrix
    cm_5class = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))

    # Binary Referable DR evaluation
    # Grade 0 & 1 = Non-referable (0)
    # Grade 2, 3, 4 = Referable DR (1)
    bin_true = (y_true >= referable_threshold).astype(int)
    bin_pred = (y_pred >= referable_threshold).astype(int)

    bin_cm = confusion_matrix(bin_true, bin_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in bin_cm.ravel()]

    sensitivity = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    referable_acc = float((tp + tn) / len(bin_true)) if len(bin_true) > 0 else 0.0
    ppv = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    npv = float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0
    referable_f1 = float((2 * tp) / (2 * tp + fp + fn)) if (2 * tp + fp + fn) > 0 else 0.0

    return {
        "total_samples": int(len(y_true)),
        "overall_accuracy": overall_acc,
        "macro_precision": macro_prec,
        "macro_recall": macro_rec,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "confusion_matrix_5class": cm_5class.tolist(),
        "per_class_report": cls_report,
        "referable_dr": {
            "referable_threshold_grade": referable_threshold,
            "positive_cases_true": int(bin_true.sum()),
            "negative_cases_true": int((1 - bin_true).sum()),
            "true_positives_tp": tp,
            "false_negatives_fn": fn,
            "true_negatives_tn": tn,
            "false_positives_fp": fp,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "accuracy": referable_acc,
            "precision_ppv": ppv,
            "npv": npv,
            "f1_score": referable_f1
        }
    }


def plot_confusion_matrices(
    y_true: Union[np.ndarray, List[int]],
    y_pred: Union[np.ndarray, List[int]],
    output_dir: Optional[Union[str, Path]] = None,
    prefix: str = "test",
    class_names: Optional[List[str]] = None,
    referable_threshold: int = 2
) -> Tuple[plt.Figure, plt.Figure]:
    """
    Plots and optionally saves both the 5-class confusion matrix
    and the binary Referable DR confusion matrix.
    """
    y_true = np.array(y_true, dtype=int)
    y_pred = np.array(y_pred, dtype=int)

    if class_names is None:
        class_names = CLASS_NAMES_SHORT

    # 1. Five-Class Matrix
    cm_5 = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    fig1, ax1 = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        cm_5,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax1
    )
    ax1.set_title(f"5-Class DR Confusion Matrix ({prefix.title()})", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Predicted Grade", fontsize=10)
    ax1.set_ylabel("True Grade", fontsize=10)
    plt.tight_layout()

    # 2. Binary Referable Matrix
    bin_true = (y_true >= referable_threshold).astype(int)
    bin_pred = (y_pred >= referable_threshold).astype(int)
    bin_cm = confusion_matrix(bin_true, bin_pred, labels=[0, 1])

    fig2, ax2 = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        bin_cm,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=["Non-Referable (<2)", "Referable DR (>=2)"],
        yticklabels=["Non-Referable (<2)", "Referable DR (>=2)"],
        ax=ax2
    )
    ax2.set_title(f"Binary Referable DR Confusion Matrix ({prefix.title()})", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Predicted Clinical Status", fontsize=10)
    ax2.set_ylabel("True Clinical Status", fontsize=10)
    plt.tight_layout()

    if output_dir is not None:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        fig1.savefig(out_p / f"{prefix}_confusion_matrix_5class.png", dpi=200)
        fig2.savefig(out_p / f"{prefix}_confusion_matrix_referable.png", dpi=200)

    return fig1, fig2


def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float, float, np.ndarray, np.ndarray, np.ndarray]:
    """
    Runs model evaluation over a PyTorch DataLoader.
    Returns: (mean_loss, accuracy, macro_f1, all_labels, all_preds, all_probs).
    """
    model.eval()
    running_loss = 0.0
    all_preds, all_labels, all_probs = [], [], []

    with torch.no_grad():
        for images, labels, _ in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            probs = torch.softmax(outputs, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)

            all_probs.extend(probs)
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    total_samples = len(dataloader.dataset)
    mean_loss = running_loss / total_samples if total_samples > 0 else 0.0

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)

    acc = float(accuracy_score(all_labels, all_preds))
    macro_f1 = float(f1_score(all_labels, all_preds, average="macro", zero_division=0))

    return mean_loss, acc, macro_f1, all_labels, all_preds, all_probs
