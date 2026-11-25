"""
Predictive confidence and uncertainty estimation for Diabetic Retinopathy screening.

Implements information-theoretic entropy, prediction margin, and top-class confidence measures
to quantify model uncertainty across multiclass (5-grade) retinal predictions.

Clinical & Ethical Guidance:
High uncertainty indicates model ambiguity or an out-of-distribution retinal image.
Uncertainty does NOT prove or disprove the presence of pathology; rather, it indicates cases
where the screening system should recommend manual clinician review instead of automated triage.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch

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


def to_numpy_probabilities(probs: Union[torch.Tensor, np.ndarray, List]) -> np.ndarray:
    """
    Safely converts input probabilities to a float32 NumPy array.
    Supports PyTorch tensors, NumPy arrays, and Python lists.
    """
    if isinstance(probs, torch.Tensor):
        return probs.detach().cpu().numpy().astype(np.float32)
    return np.asarray(probs, dtype=np.float32)


def validate_probabilities(probs: Union[torch.Tensor, np.ndarray, List]) -> np.ndarray:
    """
    Validates that the input is a valid 1D [K] or 2D [N, K] probability distribution.

    Checks:
        - Non-empty and finite (no NaN, Inf).
        - Non-negative elements.
        - Rows sum to approximately 1.0 (with automatic small-epsilon normalization).
        - At least 2 classes (K >= 2).

    Returns:
        Validated, normalized 2D NumPy array of shape [N, K].
    """
    probs_np = to_numpy_probabilities(probs)

    if probs_np.ndim == 1:
        probs_np = np.expand_dims(probs_np, axis=0)
    elif probs_np.ndim != 2:
        raise ValueError(
            f"Expected 1D [K] or 2D [N, K] probability array, got shape {probs_np.shape}"
        )

    n_samples, n_classes = probs_np.shape

    if n_samples == 0:
        raise ValueError("Probability input cannot be empty (0 samples).")
    if n_classes < 2:
        raise ValueError(f"Number of classes must be at least 2, got {n_classes}.")

    if np.isnan(probs_np).any() or np.isinf(probs_np).any():
        raise ValueError("Probability input contains NaN or Infinite values.")

    if (probs_np < 0.0).any():
        raise ValueError("Probabilities cannot contain negative values.")

    # Validate and normalize row sums
    row_sums = np.sum(probs_np, axis=1)
    if (row_sums <= 0.0).any():
        raise ValueError("Probability row sums must be strictly positive.")

    if not np.allclose(row_sums, 1.0, atol=1e-2):
        raise ValueError(
            f"Probability rows must sum to ~1.0. Found row sum range: [{np.min(row_sums):.4f}, {np.max(row_sums):.4f}]"
        )

    # Normalize slight floating-point imprecisions so sum is exactly 1.0
    normalized_probs = probs_np / np.sum(probs_np, axis=1, keepdims=True)
    return normalized_probs


def compute_entropy(
    probs: Union[torch.Tensor, np.ndarray, List],
    normalize: bool = True,
    eps: float = 1e-12
) -> np.ndarray:
    """
    Computes Shannon predictive entropy across class probabilities.

    Formula:
        H(p) = - sum_k p_k * ln(p_k + eps)
    When normalize=True:
        H_norm(p) = H(p) / ln(K) in [0.0, 1.0]

    Interpretation:
        0.0 = Complete certainty (100% confidence concentrated in one class).
        1.0 = Complete uncertainty (equal uniform probability across all K classes).

    Returns:
        1D NumPy array of shape [N] containing entropy values.
    """
    p = validate_probabilities(probs)
    n_classes = p.shape[1]

    # Clip probabilities to avoid log(0)
    p_clipped = np.clip(p, eps, 1.0)
    raw_entropy = -np.sum(p * np.log(p_clipped), axis=1)

    if normalize:
        max_entropy = np.log(n_classes)
        return (raw_entropy / max_entropy).astype(np.float32)
    return raw_entropy.astype(np.float32)


def compute_top_confidence(
    probs: Union[torch.Tensor, np.ndarray, List]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extracts the maximum predicted probability (confidence) and the corresponding class index.

    Formula:
        conf = max_k p_k,  pred = argmax_k p_k

    Returns:
        Tuple of (confidence_array [N], predicted_class_array [N])
    """
    p = validate_probabilities(probs)
    conf = np.max(p, axis=1)
    pred = np.argmax(p, axis=1)
    return conf.astype(np.float32), pred.astype(np.int64)


def compute_prediction_margin(
    probs: Union[torch.Tensor, np.ndarray, List]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes the prediction margin: the difference between the highest and second-highest
    class probabilities.

    Formula:
        margin = p_(1) - p_(2)
        margin_uncertainty = 1.0 - margin

    Interpretation:
        margin near 1.0: Model is decisively certain about the top class.
        margin near 0.0: Model is ambivalent, torn between two competing grades.

    Returns:
        Tuple of (margin [N] in [0.0, 1.0], margin_uncertainty [N] in [0.0, 1.0])
    """
    p = validate_probabilities(probs)
    # Sort probabilities descending along class axis
    sorted_p = np.sort(p, axis=1)[:, ::-1]

    top1 = sorted_p[:, 0]
    top2 = sorted_p[:, 1]

    margin = np.clip(top1 - top2, 0.0, 1.0).astype(np.float32)
    margin_uncertainty = (1.0 - margin).astype(np.float32)
    return margin, margin_uncertainty


def estimate_case_uncertainty(
    probs: Union[torch.Tensor, np.ndarray, List],
    calibrated_probs: Optional[Union[torch.Tensor, np.ndarray, List]] = None,
    uncertainty_threshold: Optional[float] = None,
    class_labels: Optional[Dict[int, str]] = None,
    is_calibrated: bool = False
) -> Dict[str, Any]:
    """
    Generates a structured uncertainty assessment for a single retinal screening case.

    Args:
        probs: 1D [K] or 2D [1, K] array of class probabilities (raw or calibrated).
        calibrated_probs: Optional calibrated probabilities from TemperatureScaler.
        uncertainty_threshold: Optional validated threshold on normalized entropy.
                               If provided, flags whether case requires human review.
        class_labels: Optional dictionary mapping class index to label string.
        is_calibrated: Whether the primary 'probs' input is already calibrated.

    Returns:
        Dict structured for consumption by integration pipeline and reporting engines.
    """
    if class_labels is None:
        class_labels = DR_GRADE_LABELS

    p = validate_probabilities(probs)
    if p.shape[0] != 1:
        raise ValueError(
            f"estimate_case_uncertainty expects a single sample [K] or [1, K], got {p.shape[0]} samples. "
            "Use estimate_batch_uncertainty for multiple cases."
        )

    p_1d = p[0]
    n_classes = len(p_1d)

    # 1. Top confidence and prediction
    conf, pred = compute_top_confidence(p)
    pred_idx = int(pred[0])
    conf_val = float(conf[0])

    # 2. Entropy measures
    raw_ent = float(compute_entropy(p, normalize=False)[0])
    norm_ent = float(compute_entropy(p, normalize=True)[0])

    # 3. Margin measures
    margin_val, margin_uncert = compute_prediction_margin(p)
    margin_val = float(margin_val[0])
    margin_uncert = float(margin_uncert[0])

    # 4. Top 2 candidate classes
    sorted_indices = np.argsort(p_1d)[::-1]
    top_2 = [
        {
            "class_index": int(idx),
            "label": class_labels.get(int(idx), f"Grade {idx}"),
            "probability": float(p_1d[idx])
        }
        for idx in sorted_indices[:2]
    ]

    # 5. Threshold evaluation (research-only; does not invent thresholds)
    requires_human_review = None
    if uncertainty_threshold is not None:
        if not (0.0 <= uncertainty_threshold <= 1.0):
            raise ValueError(f"uncertainty_threshold must be between 0.0 and 1.0, got {uncertainty_threshold}")
        requires_human_review = bool(norm_ent >= uncertainty_threshold)

    result: Dict[str, Any] = {
        "status": "success",
        "num_classes": n_classes,
        "predicted_class": pred_idx,
        "predicted_class_label": class_labels.get(pred_idx, f"Grade {pred_idx}"),
        "confidence": conf_val,
        "is_calibrated": is_calibrated,
        "uncertainty": {
            "normalized_entropy": norm_ent,
            "raw_entropy": raw_ent,
            "prediction_margin": margin_val,
            "margin_uncertainty": margin_uncert,
            "least_confidence": float(1.0 - conf_val)
        },
        "top_2_candidates": top_2,
        "class_probabilities": p_1d.tolist(),
        "policy": {
            "uncertainty_threshold": uncertainty_threshold,
            "flagged_for_human_review": requires_human_review
        }
    }

    # 6. If separate calibrated probabilities were passed, include calibration comparison
    if calibrated_probs is not None:
        p_cal = validate_probabilities(calibrated_probs)
        cal_conf, cal_pred = compute_top_confidence(p_cal)
        cal_norm_ent = float(compute_entropy(p_cal, normalize=True)[0])
        cal_margin, _ = compute_prediction_margin(p_cal)

        result["calibrated_comparison"] = {
            "calibrated_predicted_class": int(cal_pred[0]),
            "calibrated_confidence": float(cal_conf[0]),
            "calibrated_normalized_entropy": cal_norm_ent,
            "calibrated_prediction_margin": float(cal_margin[0]),
            "calibrated_probabilities": p_cal[0].tolist()
        }

    return result


def estimate_batch_uncertainty(
    probs: Union[torch.Tensor, np.ndarray, List],
    uncertainty_threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes uncertainty metrics across a batch of retinal predictions.

    Returns:
        Dict with array metrics and aggregated batch summary statistics.
    """
    p = validate_probabilities(probs)
    n_samples, n_classes = p.shape

    confs, preds = compute_top_confidence(p)
    entropies = compute_entropy(p, normalize=True)
    margins, margin_uncerts = compute_prediction_margin(p)

    flagged_mask = None
    if uncertainty_threshold is not None:
        if not (0.0 <= uncertainty_threshold <= 1.0):
            raise ValueError(f"uncertainty_threshold must be between 0.0 and 1.0, got {uncertainty_threshold}")
        flagged_mask = (entropies >= uncertainty_threshold).tolist()

    return {
        "status": "success",
        "sample_count": n_samples,
        "num_classes": n_classes,
        "predicted_classes": preds.tolist(),
        "confidences": confs.tolist(),
        "normalized_entropies": entropies.tolist(),
        "prediction_margins": margins.tolist(),
        "flagged_for_human_review": flagged_mask,
        "batch_summary": {
            "mean_confidence": float(np.mean(confs)),
            "mean_normalized_entropy": float(np.mean(entropies)),
            "mean_prediction_margin": float(np.mean(margins)),
            "percent_uncertain": float(np.mean(flagged_mask) * 100.0) if flagged_mask is not None else None
        }
    }
