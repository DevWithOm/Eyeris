"""
Confidence calibration routines for Diabetic Retinopathy classification models.

Implements Temperature Scaling (Guo et al., 2017) and evaluation metrics including
Expected Calibration Error (ECE), Maximum Calibration Error (MCE), and multiclass Brier Score.

Clinical Relevance:
Deep neural networks are typically overconfident. Calibration aligns the model's predicted
confidence probabilities with its true empirical accuracy without altering its predictions or accuracy.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

try:
    from ai_models.common.labels import DR_GRADE_LABELS
except ImportError:
    DR_GRADE_LABELS = {
        0: "No DR",
        1: "Mild",
        2: "Moderate",
        3: "Severe",
        4: "Proliferative DR"
    }


def to_tensor(arr: Union[torch.Tensor, np.ndarray, List], dtype=torch.float32) -> torch.Tensor:
    """Safely converts input array, list, or tensor to a PyTorch tensor."""
    if isinstance(arr, torch.Tensor):
        return arr.to(dtype=dtype)
    return torch.tensor(np.asarray(arr), dtype=dtype)


def to_numpy(arr: Union[torch.Tensor, np.ndarray, List], dtype=np.float32) -> np.ndarray:
    """Safely converts input array, list, or tensor to a NumPy ndarray."""
    if isinstance(arr, torch.Tensor):
        return arr.detach().cpu().numpy().astype(dtype)
    return np.asarray(arr, dtype=dtype)


def validate_logits_and_labels(
    logits: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validates shapes and values for logits [N, num_classes] and ground-truth labels [N].

    Returns:
        Tuple of (validated_logits_np, validated_labels_np)

    Raises:
        ValueError: If dimensions mismatch, inputs are empty, or labels are out of bounds.
    """
    logits_np = to_numpy(logits, dtype=np.float32)
    labels_np = to_numpy(labels, dtype=np.int64)

    if logits_np.ndim != 2:
        raise ValueError(f"Expected 2D logits of shape [N, num_classes], got shape {logits_np.shape}")
    if labels_np.ndim != 1:
        raise ValueError(f"Expected 1D labels of shape [N], got shape {labels_np.shape}")

    n_samples, n_classes = logits_np.shape

    if n_samples == 0:
        raise ValueError("Inputs cannot be empty (0 samples).")
    if n_classes < 2:
        raise ValueError(f"Number of classes must be at least 2, got {n_classes}.")
    if len(labels_np) != n_samples:
        raise ValueError(
            f"Sample count mismatch: logits has {n_samples} samples, labels has {len(labels_np)}."
        )

    if np.isnan(logits_np).any() or np.isinf(logits_np).any():
        raise ValueError("Logits contain NaN or Infinite values.")

    min_lbl, max_lbl = int(np.min(labels_np)), int(np.max(labels_np))
    if min_lbl < 0 or max_lbl >= n_classes:
        raise ValueError(
            f"Label values out of range: labels must be in [0, {n_classes - 1}], "
            f"found range [{min_lbl}, {max_lbl}]."
        )

    return logits_np, labels_np


def compute_ece(
    probs: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray],
    n_bins: int = 10
) -> float:
    """
    Computes Expected Calibration Error (ECE).
    Partitions predictions into equally spaced confidence bins and calculates
    the weighted average difference between confidence and accuracy.

    Formula:
        ECE = sum_m (|B_m| / N) * |acc(B_m) - conf(B_m)|

    Args:
        probs: 2D array [N, num_classes] of predicted softmax probabilities.
        labels: 1D array [N] of true class integer labels.
        n_bins: Number of confidence bins (typically 10 or 15).

    Returns:
        ECE as a float in [0.0, 1.0]. Lower is better.
    """
    if n_bins <= 0:
        raise ValueError(f"n_bins must be a positive integer, got {n_bins}")

    probs_np = to_numpy(probs, dtype=np.float32)
    labels_np = to_numpy(labels, dtype=np.int64)

    confidences = np.max(probs_np, axis=1)
    predictions = np.argmax(probs_np, axis=1)
    accuracies = (predictions == labels_np).astype(np.float32)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    n_samples = len(labels_np)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # First bin is inclusive of 0.0; subsequent bins are (lower, upper]
        if i == 0:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)

        bin_count = np.sum(in_bin)
        if bin_count > 0:
            bin_acc = np.mean(accuracies[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            ece += (bin_count / n_samples) * np.abs(bin_acc - bin_conf)

    return float(ece)


def compute_mce(
    probs: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray],
    n_bins: int = 10
) -> float:
    """
    Computes Maximum Calibration Error (MCE).
    Calculates the maximum calibration error across all non-empty confidence bins.

    Formula:
        MCE = max_m |acc(B_m) - conf(B_m)|
    """
    if n_bins <= 0:
        raise ValueError(f"n_bins must be a positive integer, got {n_bins}")

    probs_np = to_numpy(probs, dtype=np.float32)
    labels_np = to_numpy(labels, dtype=np.int64)

    confidences = np.max(probs_np, axis=1)
    predictions = np.argmax(probs_np, axis=1)
    accuracies = (predictions == labels_np).astype(np.float32)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    mce = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == 0:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)

        bin_count = np.sum(in_bin)
        if bin_count > 0:
            bin_acc = np.mean(accuracies[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            gap = np.abs(bin_acc - bin_conf)
            if gap > mce:
                mce = gap

    return float(mce)


def compute_brier_score(
    probs: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray]
) -> float:
    """
    Computes the multiclass Brier score (mean squared error of probability forecasts).

    Formula:
        Brier = (1 / N) * sum_i sum_k (p_ik - y_ik)^2
    where y_ik is 1 if true class is k, else 0.

    Returns:
        Brier score float in [0.0, 2.0]. Lower is better.
    """
    probs_np = to_numpy(probs, dtype=np.float32)
    labels_np = to_numpy(labels, dtype=np.int64)

    n_samples, n_classes = probs_np.shape

    # One-hot encode ground truth labels
    one_hot = np.zeros((n_samples, n_classes), dtype=np.float32)
    one_hot[np.arange(n_samples), labels_np] = 1.0

    squared_errors = np.sum((probs_np - one_hot) ** 2, axis=1)
    return float(np.mean(squared_errors))


def compute_nll(
    logits: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray]
) -> float:
    """
    Computes multiclass Negative Log-Likelihood (Cross-Entropy loss).
    """
    logits_t = to_tensor(logits, dtype=torch.float32)
    labels_t = to_tensor(labels, dtype=torch.int64)
    loss = nn.CrossEntropyLoss()(logits_t, labels_t)
    return float(loss.item())


def compute_reliability_diagram(
    probs: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray],
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Computes per-bin accuracy and confidence statistics for plotting a Reliability Diagram.
    """
    probs_np = to_numpy(probs, dtype=np.float32)
    labels_np = to_numpy(labels, dtype=np.int64)

    confidences = np.max(probs_np, axis=1)
    predictions = np.argmax(probs_np, axis=1)
    accuracies = (predictions == labels_np).astype(np.float32)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    bin_accs = []
    bin_confs = []
    bin_counts = []

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == 0:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
        else:
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)

        count = int(np.sum(in_bin))
        bin_counts.append(count)

        if count > 0:
            bin_accs.append(float(np.mean(accuracies[in_bin])))
            bin_confs.append(float(np.mean(confidences[in_bin])))
        else:
            bin_accs.append(0.0)
            bin_confs.append(float((bin_lower + bin_upper) / 2.0))

    return {
        "n_bins": n_bins,
        "bin_boundaries": bin_boundaries.tolist(),
        "bin_accuracies": bin_accs,
        "bin_confidences": bin_confs,
        "bin_counts": bin_counts,
        "ece": compute_ece(probs_np, labels_np, n_bins=n_bins),
        "mce": compute_mce(probs_np, labels_np, n_bins=n_bins),
    }


class TemperatureScaler(nn.Module):
    """
    Temperature Scaling post-processing calibrator for PyTorch classification models.

    Temperature scaling applies a single learned positive scalar parameter T > 0:
        p_i = softmax(z_i / T)
    Optimizes Negative Log-Likelihood on a held-out validation dataset via L-BFGS.
    Does not change argmax predictions or top-1 accuracy.
    """
    def __init__(self, initial_temperature: float = 1.5):
        super().__init__()
        if initial_temperature <= 0:
            raise ValueError(f"Initial temperature must be positive, got {initial_temperature}")
        self.temperature = nn.Parameter(torch.ones(1) * float(initial_temperature))
        self.is_fitted: bool = False

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        """Scales logits by dividing by the learned temperature T."""
        return logits / torch.clamp(self.temperature, min=1e-3)

    def predict_proba(
        self,
        logits: Union[torch.Tensor, np.ndarray]
    ) -> np.ndarray:
        """
        Scales logits by temperature and returns calibrated softmax probabilities.
        """
        logits_t = to_tensor(logits, dtype=torch.float32)
        with torch.no_grad():
            scaled = self.forward(logits_t)
            probs = torch.softmax(scaled, dim=-1)
        return probs.cpu().numpy()

    def fit(
        self,
        val_logits: Union[torch.Tensor, np.ndarray],
        val_labels: Union[torch.Tensor, np.ndarray],
        lr: float = 0.05,
        max_iter: int = 50
    ) -> "TemperatureScaler":
        """
        Optimizes the temperature parameter T to minimize Negative Log-Likelihood
        on a validation set (preventing data leakage into the test set).

        Args:
            val_logits: 2D array/tensor [N_val, num_classes] of uncalibrated model logits.
            val_labels: 1D array/tensor [N_val] of true integer class labels.
            lr: Learning rate for L-BFGS optimizer.
            max_iter: Maximum number of L-BFGS iterations.

        Returns:
            self: The fitted TemperatureScaler instance.
        """
        val_logits_np, val_labels_np = validate_logits_and_labels(val_logits, val_labels)

        logits_t = torch.tensor(val_logits_np, dtype=torch.float32)
        labels_t = torch.tensor(val_labels_np, dtype=torch.int64)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.LBFGS([self.temperature], lr=lr, max_iter=max_iter)

        def eval_step():
            optimizer.zero_grad()
            # Ensure temperature stays positive
            with torch.no_grad():
                self.temperature.clamp_(min=1e-3)
            loss = criterion(self.forward(logits_t), labels_t)
            loss.backward()
            return loss

        optimizer.step(eval_step)

        # Enforce positive temperature
        with torch.no_grad():
            self.temperature.clamp_(min=1e-3)

        self.is_fitted = True
        return self

    def save(self, filepath: Union[str, Path]) -> str:
        """Saves temperature calibration metadata to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "method": "temperature_scaling",
            "temperature": float(self.temperature.item()),
            "is_fitted": self.is_fitted
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return str(path.resolve())

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "TemperatureScaler":
        """Loads a saved TemperatureScaler from JSON metadata."""
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Calibration file not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        temp_val = float(data.get("temperature", 1.0))
        scaler = cls(initial_temperature=temp_val)
        scaler.is_fitted = bool(data.get("is_fitted", True))
        return scaler


def evaluate_calibration(
    logits: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray],
    temperature: float = 1.0,
    n_bins: int = 10
) -> Dict[str, float]:
    """
    Computes comprehensive calibration metrics for a set of logits at a specified temperature.
    """
    logits_np, labels_np = validate_logits_and_labels(logits, labels)

    if temperature <= 0:
        raise ValueError(f"Temperature must be positive, got {temperature}")

    scaled_logits = logits_np / temperature
    exp_logits = np.exp(scaled_logits - np.max(scaled_logits, axis=1, keepdims=True))
    probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    preds = np.argmax(probs, axis=1)
    acc = float(np.mean(preds == labels_np))
    confidences = np.max(probs, axis=1)
    mean_conf = float(np.mean(confidences))

    ece = compute_ece(probs, labels_np, n_bins=n_bins)
    mce = compute_mce(probs, labels_np, n_bins=n_bins)
    brier = compute_brier_score(probs, labels_np)
    nll = compute_nll(scaled_logits, labels_np)

    return {
        "temperature": float(temperature),
        "ece": ece,
        "mce": mce,
        "brier_score": brier,
        "nll": nll,
        "accuracy": acc,
        "mean_confidence": mean_conf
    }


def compare_calibration(
    val_logits: Union[torch.Tensor, np.ndarray],
    val_labels: Union[torch.Tensor, np.ndarray],
    test_logits: Union[torch.Tensor, np.ndarray],
    test_labels: Union[torch.Tensor, np.ndarray],
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Fits Temperature Scaling on validation logits and evaluates performance on held-out test logits.
    Guarantees no data leakage by maintaining strict separation between validation and test sets.

    Returns:
        Structured comparison of uncalibrated vs calibrated metrics on the test set.
    """
    # 1. Fit scaler strictly on validation split
    scaler = TemperatureScaler(initial_temperature=1.5)
    scaler.fit(val_logits, val_labels)
    optimal_t = float(scaler.temperature.item())

    # 2. Evaluate uncalibrated (T=1.0) and calibrated (T=optimal_t) on test split
    uncalibrated = evaluate_calibration(test_logits, test_labels, temperature=1.0, n_bins=n_bins)
    calibrated = evaluate_calibration(test_logits, test_labels, temperature=optimal_t, n_bins=n_bins)

    ece_reduction = float(uncalibrated["ece"] - calibrated["ece"])
    brier_reduction = float(uncalibrated["brier_score"] - calibrated["brier_score"])
    nll_reduction = float(uncalibrated["nll"] - calibrated["nll"])

    return {
        "status": "success",
        "optimal_temperature": optimal_t,
        "uncalibrated": uncalibrated,
        "calibrated": calibrated,
        "improvements": {
            "ece_reduction": ece_reduction,
            "brier_reduction": brier_reduction,
            "nll_reduction": nll_reduction,
            "accuracy_preserved": (uncalibrated["accuracy"] == calibrated["accuracy"])
        }
    }
