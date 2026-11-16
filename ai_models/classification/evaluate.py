"""
Evaluation protocol and classification metrics for Diabetic Retinopathy screening.

Implements multi-class and clinical referable metrics adhering to docs/evaluation_protocol.md:
- Confusion Matrix (5x5 for Eyeris grades 0-4)
- Macro and Weighted Precision, Recall, F1
- Per-class metrics with support tracking
- Clinical Referable DR metrics: Sensitivity, Specificity, PPV, NPV, Binary Accuracy
- Quadratic Weighted Kappa
- External dataset label schema validation and mapping
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

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

EYERIS_NUM_CLASSES = 5


def to_numpy_1d(arr: Union[torch.Tensor, np.ndarray, List], dtype=np.int64) -> np.ndarray:
    """Safely converts input array, list, or tensor to a 1D NumPy array."""
    if isinstance(arr, torch.Tensor):
        arr_np = arr.detach().cpu().numpy()
    else:
        arr_np = np.asarray(arr)

    arr_squeezed = np.squeeze(arr_np)
    if arr_squeezed.ndim == 0 and arr_np.size == 1:
        return arr_np.reshape(-1).astype(dtype)
    return arr_squeezed.astype(dtype)


def validate_evaluation_inputs(
    y_true: Union[torch.Tensor, np.ndarray, List],
    y_pred: Union[torch.Tensor, np.ndarray, List],
    num_classes: int = EYERIS_NUM_CLASSES
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validates true and predicted labels for classification evaluation.

    Raises:
        ValueError: If inputs are empty, dimensions are wrong, sample lengths mismatch,
                    NaNs/Infs are present, or labels are out of bounds.
    """
    # Check for NaNs before casting
    true_raw = np.asarray(y_true.detach().cpu().numpy() if isinstance(y_true, torch.Tensor) else y_true)
    pred_raw = np.asarray(y_pred.detach().cpu().numpy() if isinstance(y_pred, torch.Tensor) else y_pred)

    if np.isnan(true_raw).any() or np.isnan(pred_raw).any():
        raise ValueError("Evaluation labels contain NaN values.")
    if np.isinf(true_raw).any() or np.isinf(pred_raw).any():
        raise ValueError("Evaluation labels contain Infinite values.")

    true_np = to_numpy_1d(y_true, dtype=np.int64)
    pred_np = to_numpy_1d(y_pred, dtype=np.int64)

    if true_np.ndim != 1 or pred_np.ndim != 1:
        raise ValueError(
            f"Expected 1D label vectors, got y_true.ndim={true_np.ndim}, y_pred.ndim={pred_np.ndim}"
        )

    if len(true_np) == 0:
        raise ValueError("Evaluation arrays cannot be empty (0 samples).")

    if len(true_np) != len(pred_np):
        raise ValueError(
            f"Sample length mismatch: y_true has {len(true_np)} samples, y_pred has {len(pred_np)} samples."
        )

    min_t, max_t = int(np.min(true_np)), int(np.max(true_np))
    min_p, max_p = int(np.min(pred_np)), int(np.max(pred_np))

    if min_t < 0 or max_t >= num_classes:
        raise ValueError(
            f"y_true label values out of bounds: must be in [0, {num_classes - 1}], found [{min_t}, {max_t}]."
        )
    if min_p < 0 or max_p >= num_classes:
        raise ValueError(
            f"y_pred label values out of bounds: must be in [0, {num_classes - 1}], found [{min_p}, {max_p}]."
        )

    return true_np, pred_np


def compute_classification_metrics(
    y_true: Union[torch.Tensor, np.ndarray, List],
    y_pred: Union[torch.Tensor, np.ndarray, List],
    y_probs: Optional[Union[torch.Tensor, np.ndarray, List]] = None,
    class_names: Optional[Dict[int, str]] = None,
    referable_threshold: int = 2
) -> Dict[str, Any]:
    """
    Computes comprehensive multiclass and clinical referable metrics adhering to docs/evaluation_protocol.md.

    Args:
        y_true: Ground-truth integer labels [N] (0 to 4).
        y_pred: Model predicted integer labels [N] (0 to 4).
        y_probs: Optional predicted probabilities [N, 5].
        class_names: Optional mapping of class indices to human-readable strings.
        referable_threshold: Grade threshold for Referable DR (default: 2, meaning Grades 2-4 are Referable).

    Returns:
        Structured evaluation dictionary containing:
            - overall_accuracy, macro_precision, macro_recall, macro_f1, weighted_f1
            - quadratic_weighted_kappa
            - confusion_matrix_5class (always 5x5 list of lists)
            - per_class: per-grade precision, recall, f1, support
            - referable_dr: clinical binary metrics (sensitivity, specificity, PPV, NPV, accuracy)
            - evaluation_metadata
    """
    if class_names is None:
        class_names = DR_GRADE_LABELS

    true_np, pred_np = validate_evaluation_inputs(y_true, y_pred, num_classes=EYERIS_NUM_CLASSES)
    n_samples = len(true_np)

    # 1. Multiclass Overall Metrics
    acc = float(accuracy_score(true_np, pred_np))
    macro_prec = float(precision_score(true_np, pred_np, average="macro", zero_division=0))
    macro_rec = float(recall_score(true_np, pred_np, average="macro", zero_division=0))
    macro_f1 = float(f1_score(true_np, pred_np, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(true_np, pred_np, average="weighted", zero_division=0))

    # 2. Quadratic Weighted Kappa (QWK)
    # QWK measures inter-rater agreement for ordinal classification (punishing distant grade errors).
    try:
        qwk = float(cohen_kappa_score(true_np, pred_np, weights="quadratic"))
        if np.isnan(qwk):
            qwk = None
    except Exception:
        qwk = None

    # 3. Fixed 5x5 Confusion Matrix
    all_classes = list(range(EYERIS_NUM_CLASSES))
    cm_5x5 = confusion_matrix(true_np, pred_np, labels=all_classes)

    # 4. Per-Class Precision, Recall, F1, and Support
    per_class_prec = precision_score(true_np, pred_np, labels=all_classes, average=None, zero_division=0)
    per_class_rec = recall_score(true_np, pred_np, labels=all_classes, average=None, zero_division=0)
    per_class_f1 = f1_score(true_np, pred_np, labels=all_classes, average=None, zero_division=0)

    per_class_dict = {}
    for c in all_classes:
        support = int(np.sum(true_np == c))
        predicted_count = int(np.sum(pred_np == c))
        c_name = class_names.get(c, f"Grade {c}")
        per_class_dict[c_name] = {
            "class_index": c,
            "support": support,
            "predicted_count": predicted_count,
            "precision": float(per_class_prec[c]) if (predicted_count > 0 or support > 0) else None,
            "recall": float(per_class_rec[c]) if support > 0 else None,
            "f1_score": float(per_class_f1[c]) if support > 0 else None,
        }

    # 5. Clinical Referable DR Evaluation
    # Grade 0 & 1 -> Non-Referable (0)
    # Grade 2, 3, 4 -> Referable DR (1)
    bin_true = (true_np >= referable_threshold).astype(int)
    bin_pred = (pred_np >= referable_threshold).astype(int)

    bin_cm = confusion_matrix(bin_true, bin_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in bin_cm.ravel()]

    pos_true = tp + fn
    neg_true = tn + fp
    pos_pred = tp + fp
    neg_pred = tn + fn

    # Distinguish unavailable metrics (None) from zero metrics (0.0)
    sensitivity = float(tp / pos_true) if pos_true > 0 else None
    specificity = float(tn / neg_true) if neg_true > 0 else None
    ppv = float(tp / pos_pred) if pos_pred > 0 else None
    npv = float(tn / neg_pred) if neg_pred > 0 else None
    referable_acc = float((tp + tn) / n_samples)
    referable_f1 = float((2 * tp) / (2 * tp + fp + fn)) if (2 * tp + fp + fn) > 0 else 0.0

    results: Dict[str, Any] = {
        "status": "success",
        "sample_count": n_samples,
        "num_classes": EYERIS_NUM_CLASSES,
        "multiclass": {
            "overall_accuracy": acc,
            "macro_precision": macro_prec,
            "macro_recall": macro_rec,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "quadratic_weighted_kappa": qwk,
            "confusion_matrix_5class": cm_5x5.tolist(),
            "per_class": per_class_dict
        },
        "referable_dr": {
            "referable_threshold_grade": referable_threshold,
            "true_positives_tp": tp,
            "false_positives_fp": fp,
            "true_negatives_tn": tn,
            "false_negatives_fn": fn,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "precision_ppv": ppv,
            "npv": npv,
            "binary_accuracy": referable_acc,
            "f1_score": referable_f1
        },
        "metadata": {
            "evaluation_standard": "docs/evaluation_protocol.md",
            "has_probabilities": y_probs is not None
        }
    }

    return results


def map_external_dataset_labels(
    labels: Union[torch.Tensor, np.ndarray, List],
    dataset_name: str,
    label_mapping: Optional[Dict[Any, int]] = None
) -> np.ndarray:
    """
    Validates and maps external dataset labels into the project's standardized label schema.

    Supported standard datasets:
        - 'aptos_2019': 5-grade integer scale (0-4). Identity mapping.
        - 'idrid': 5-grade integer scale (0-4). Identity mapping.
        - 'messidor_2_referable': Binary mapping {0: 0, 1: 0, 2: 1, 3: 1}.
        - 'messidor_2': Requires explicit label_mapping because Messidor-2 uses a 4-grade scale (0-3)
                        that cannot be unambiguously mapped to the 5-grade ICDR scale without clinical policy.

    Args:
        labels: 1D array of external labels.
        dataset_name: Name of the external dataset source.
        label_mapping: Optional custom dictionary mapping source labels to target integers.

    Returns:
        1D NumPy array of mapped integer labels.

    Raises:
        ValueError: If labels cannot be mapped, dataset is unsupported, or mapped labels are out of range.
    """
    labels_np = to_numpy_1d(labels, dtype=np.int64)
    name_clean = dataset_name.strip().lower()

    if label_mapping is not None:
        mapped = []
        for val in labels_np:
            if val not in label_mapping:
                raise ValueError(
                    f"Label value {val} not found in user-supplied label_mapping: {list(label_mapping.keys())}"
                )
            mapped.append(int(label_mapping[val]))
        return np.array(mapped, dtype=np.int64)

    if name_clean in ["aptos", "aptos_2019", "aptos2019", "idrid"]:
        # Standard 5-grade ICDR datasets
        min_val, max_val = int(np.min(labels_np)), int(np.max(labels_np))
        if min_val < 0 or max_val >= EYERIS_NUM_CLASSES:
            raise ValueError(
                f"Dataset '{dataset_name}' labels must be in range [0, 4], found [{min_val}, {max_val}]."
            )
        return labels_np.copy()

    elif name_clean == "messidor_2_referable":
        # Binary Referable mapping: Grades 0-1 -> 0 (Non-Referable), Grades 2-3 -> 1 (Referable)
        mapping = {0: 0, 1: 0, 2: 1, 3: 1}
        mapped = []
        for val in labels_np:
            if val not in mapping:
                raise ValueError(f"Unexpected Messidor-2 label value: {val}. Expected one of {list(mapping.keys())}")
            mapped.append(mapping[val])
        return np.array(mapped, dtype=np.int64)

    elif name_clean in ["messidor", "messidor_2", "messidor2"]:
        raise ValueError(
            "Messidor-2 labels (0-3) cannot be unambiguously mapped to the 5-grade Eyeris scale "
            "without an explicit 'label_mapping' dictionary. Messidor Grade 3 merges severe non-proliferative "
            "and proliferative retinopathy. To perform binary referable screening evaluation, use "
            "dataset_name='messidor_2_referable' or supply a documented label_mapping dict."
        )

    else:
        raise ValueError(
            f"Unsupported external dataset: '{dataset_name}'. "
            f"Supported presets: 'aptos_2019', 'idrid', 'messidor_2_referable', or supply explicit 'label_mapping'."
        )
