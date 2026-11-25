"""
Diabetic Retinopathy Classification Model Evaluation & Metrics.

Unified evaluation module integrating:
- Statistical metrics computation & schema validation (Siddhi-Garg)
- Held-out test split benchmarking, confusion matrix generation & artifact export (Shourya)
Adheres to docs/evaluation_protocol.md and docs/integration_contract.md.
"""

import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Non-interactive background rendering
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)

# Project paths & imports
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from ai_models.common.labels import DR_GRADE_LABELS
except ImportError:
    DR_GRADE_LABELS = {
        0: "No DR",
        1: "Mild",
        2: "Moderate",
        3: "Severe",
        4: "Proliferative DR",
    }

try:
    from ai_models.classification.model import DEFAULT_CHECKPOINT_PATH
except ImportError:
    DEFAULT_CHECKPOINT_PATH = _PROJECT_ROOT / "artifacts" / "model_weights" / "best_model.pth"

try:
    from ai_models.classification.predict import predict_grade
except ImportError:
    predict_grade = None

EYERIS_NUM_CLASSES = 5

DEFAULT_SPLIT_PATH = _PROJECT_ROOT / "data" / "manifests" / "test_split.csv"
FALLBACK_SPLIT_PATH = Path(r"E:\Minor Project\DR_Classification_Project_Template\data\splits\test_split.csv")
DEFAULT_IMG_DIR = Path(r"E:\DR_Classification_Project_Template\data\raw\aptos\train_images")
DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "artifacts" / "evaluation"


# =====================================================================
# 1. Metric Calculation & Schema Validation Utilities (Siddhi-Garg)
# =====================================================================

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
    num_classes: int = EYERIS_NUM_CLASSES,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validates true and predicted labels for classification evaluation.

    Raises:
        ValueError: If inputs are empty, dimensions are wrong, sample lengths mismatch,
                    NaNs/Infs are present, or labels are out of bounds.
    """
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
    referable_threshold: int = 2,
) -> Dict[str, Any]:
    """
    Computes comprehensive multiclass and clinical referable metrics adhering to docs/evaluation_protocol.md.
    """
    true_np, pred_np = validate_evaluation_inputs(y_true, y_pred, num_classes=EYERIS_NUM_CLASSES)
    n_samples = len(true_np)

    names = class_names or DR_GRADE_LABELS

    # Multiclass Metrics
    acc = float(accuracy_score(true_np, pred_np))
    macro_prec = float(precision_score(true_np, pred_np, average="macro", zero_division=0))
    macro_rec = float(recall_score(true_np, pred_np, average="macro", zero_division=0))
    macro_f1 = float(f1_score(true_np, pred_np, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(true_np, pred_np, average="weighted", zero_division=0))

    qwk = float(cohen_kappa_score(true_np, pred_np, weights="quadratic"))

    cm_5x5 = confusion_matrix(true_np, pred_np, labels=list(range(EYERIS_NUM_CLASSES)))

    prec_per_class, rec_per_class, f1_per_class, supp_per_class = precision_recall_fscore_support(
        true_np, pred_np, labels=list(range(EYERIS_NUM_CLASSES)), zero_division=0
    )

    per_class_dict = {}
    for c in range(EYERIS_NUM_CLASSES):
        c_name = names.get(c, f"Grade {c}")
        per_class_dict[f"class_{c}"] = {
            "grade_index": c,
            "label_name": c_name,
            "precision": float(prec_per_class[c]),
            "recall": float(rec_per_class[c]),
            "f1_score": float(f1_per_class[c]),
            "support": int(supp_per_class[c]),
        }

    # Clinical Referable DR Metrics
    true_ref = (true_np >= referable_threshold).astype(np.int64)
    pred_ref = (pred_np >= referable_threshold).astype(np.int64)

    tp = int(np.sum((true_ref == 1) & (pred_ref == 1)))
    fp = int(np.sum((true_ref == 0) & (pred_ref == 1)))
    tn = int(np.sum((true_ref == 0) & (pred_ref == 0)))
    fn = int(np.sum((true_ref == 1) & (pred_ref == 0)))

    pos_true = tp + fn
    neg_true = tn + fp
    pos_pred = tp + fp
    neg_pred = tn + fn

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
            "per_class": per_class_dict,
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
            "f1_score": referable_f1,
        },
        "metadata": {
            "evaluation_standard": "docs/evaluation_protocol.md",
            "has_probabilities": y_probs is not None,
        },
    }

    return results


def map_external_dataset_labels(
    labels: Union[torch.Tensor, np.ndarray, List],
    dataset_name: str,
    label_mapping: Optional[Dict[Any, int]] = None,
) -> np.ndarray:
    """
    Validates and maps external dataset labels into the project's standardized label schema.
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
        min_val, max_val = int(np.min(labels_np)), int(np.max(labels_np))
        if min_val < 0 or max_val >= EYERIS_NUM_CLASSES:
            raise ValueError(
                f"Dataset '{dataset_name}' labels must be in range [0, 4], found [{min_val}, {max_val}]."
            )
        return labels_np.copy()

    elif name_clean == "messidor_2_referable":
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


# =====================================================================
# 2. Held-out Test Evaluation Runner & Plotting (Shourya)
# =====================================================================

def verify_evaluation_assets(
    split_path: Path,
    img_dir: Path,
    checkpoint_path: Path,
) -> pd.DataFrame:
    """
    Verifies that all required evaluation assets (split manifest, images, checkpoint)
    are present and consistent before running evaluation.
    """
    print("=" * 65)
    print("PRE-EVALUATION ASSET INTEGRITY VERIFICATION")
    print("=" * 65)

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {checkpoint_path}")
    print(f"[OK] Checkpoint found: {checkpoint_path} ({checkpoint_path.stat().st_size / (1024*1024):.2f} MB)")

    if not split_path.exists():
        raise FileNotFoundError(f"Original test split manifest not found at: {split_path}")
    print(f"[OK] Split manifest found: {split_path}")

    df = pd.read_csv(split_path)
    required_cols = {"id_code", "diagnosis"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Manifest missing required columns. Expected {required_cols}, found {df.columns.tolist()}")

    if not img_dir.exists():
        raise FileNotFoundError(f"Image directory not found at: {img_dir}")
    print(f"[OK] Image directory found: {img_dir}")

    missing_images = []
    for id_code in df["id_code"]:
        img_file = img_dir / f"{id_code}.png"
        if not img_file.exists():
            missing_images.append(str(id_code))

    if missing_images:
        raise FileNotFoundError(
            f"Missing {len(missing_images)} test images in {img_dir}. First 5: {missing_images[:5]}"
        )
    print(f"[OK] All {len(df)} test images confirmed present on disk.")

    print("\nHeld-out Test Set Class Distribution:")
    counts = df["diagnosis"].value_counts().sort_index()
    for grade, count in counts.items():
        pct = (count / len(df)) * 100
        print(f"  Grade {grade} ({DR_GRADE_LABELS.get(grade, 'Unknown')}): {count:4d} images ({pct:5.1f}%)")
    print(f"  Total test samples: {len(df)}")
    print("=" * 65 + "\n")

    return df


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    output_path: Path,
    title: str = "Diabetic Retinopathy Confusion Matrix",
) -> None:
    """
    Renders and saves a formatted confusion matrix plot.
    """
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=class_names,
        yticklabels=class_names,
        title=title,
        ylabel="True Diagnosis Grade",
        xlabel="Predicted Diagnosis Grade",
    )

    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor")

    thresh = cm.max() / 2.0
    cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            count = cm[i, j]
            pct = cm_norm[i, j] * 100
            text = f"{count}\n({pct:.1f}%)"
            ax.text(
                j, i, text,
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=9,
            )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Saved Confusion Matrix to {output_path}")


def run_test_evaluation(
    split_path: Optional[Union[str, Path]] = None,
    img_dir: Optional[Union[str, Path]] = None,
    checkpoint_path: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> Dict:
    """
    Runs evaluation over the full held-out test split using the exact inference pipeline.
    """
    if predict_grade is None:
        raise ImportError("Cannot run test evaluation: predict_grade function is unavailable.")

    resolved_split = Path(split_path) if split_path else (
        DEFAULT_SPLIT_PATH if DEFAULT_SPLIT_PATH.exists() else FALLBACK_SPLIT_PATH
    )
    resolved_img_dir = Path(img_dir) if img_dir else DEFAULT_IMG_DIR
    resolved_checkpoint = Path(checkpoint_path) if checkpoint_path else DEFAULT_CHECKPOINT_PATH
    resolved_output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    df_test = verify_evaluation_assets(resolved_split, resolved_img_dir, resolved_checkpoint)

    print(f"Running inference on {len(df_test)} held-out test images...")
    predictions = []
    start_time = time.time()

    for idx, row in df_test.iterrows():
        id_code = str(row["id_code"]).strip()
        true_grade = int(row["diagnosis"])
        img_path = resolved_img_dir / f"{id_code}.png"

        res = predict_grade(str(img_path), checkpoint_path=resolved_checkpoint)

        probs = res["probabilities"]
        pred_grade = int(res["predicted_grade"])

        record = {
            "id_code": id_code,
            "true_grade": true_grade,
            "true_name": DR_GRADE_LABELS.get(true_grade, f"Grade {true_grade}"),
            "predicted_grade": pred_grade,
            "predicted_name": res["grade_name"],
            "correct": bool(pred_grade == true_grade),
            "raw_confidence": float(res["raw_confidence"]),
            "prob_0": float(probs[0]),
            "prob_1": float(probs[1]),
            "prob_2": float(probs[2]),
            "prob_3": float(probs[3]),
            "prob_4": float(probs[4]),
        }
        predictions.append(record)

        if (idx + 1) % 50 == 0 or (idx + 1) == len(df_test):
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed
            print(f"  [{idx + 1:3d}/{len(df_test)}] images processed ({rate:.1f} imgs/s)")

    total_time = time.time() - start_time
    print(f"\nInference completed in {total_time:.2f}s ({total_time / len(df_test):.3f}s/image).")

    df_preds = pd.DataFrame(predictions)
    pred_csv_path = resolved_output_dir / "test_predictions.csv"
    df_preds.to_csv(pred_csv_path, index=False)
    print(f"[OK] Saved per-image predictions to {pred_csv_path}")

    y_true = df_preds["true_grade"].to_numpy()
    y_pred = df_preds["predicted_grade"].to_numpy()

    accuracy = float(accuracy_score(y_true, y_pred))
    qwk = float(cohen_kappa_score(y_true, y_pred, weights="quadratic"))

    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )

    per_class_p, per_class_r, per_class_f1, per_class_support = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=[0, 1, 2, 3, 4], zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3, 4])

    y_true_ref = (y_true >= 2).astype(int)
    y_pred_ref = (y_pred >= 2).astype(int)

    tp = int(np.sum((y_true_ref == 1) & (y_pred_ref == 1)))
    tn = int(np.sum((y_true_ref == 0) & (y_pred_ref == 0)))
    fp = int(np.sum((y_true_ref == 0) & (y_pred_ref == 1)))
    fn = int(np.sum((y_true_ref == 1) & (y_pred_ref == 0)))

    ref_sensitivity = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    ref_specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    ref_accuracy = float((tp + tn) / len(y_true))
    ref_f1 = float(f1_score(y_true_ref, y_pred_ref, zero_division=0))

    class_report_rows = []
    class_names = [f"Grade {c} ({DR_GRADE_LABELS[c]})" for c in range(5)]
    for c in range(5):
        class_report_rows.append({
            "class": f"Grade {c} ({DR_GRADE_LABELS[c]})",
            "precision": float(per_class_p[c]),
            "recall": float(per_class_r[c]),
            "f1_score": float(per_class_f1[c]),
            "support": int(per_class_support[c]),
        })

    class_report_rows.append({
        "class": "macro avg",
        "precision": float(macro_p),
        "recall": float(macro_r),
        "f1_score": float(macro_f1),
        "support": int(len(y_true)),
    })
    class_report_rows.append({
        "class": "weighted avg",
        "precision": float(weighted_p),
        "recall": float(weighted_r),
        "f1_score": float(weighted_f1),
        "support": int(len(y_true)),
    })

    df_report = pd.DataFrame(class_report_rows)
    report_csv_path = resolved_output_dir / "classification_report.csv"
    df_report.to_csv(report_csv_path, index=False)
    print(f"[OK] Saved classification report to {report_csv_path}")

    cm_plot_path = resolved_output_dir / "confusion_matrix.png"
    plot_confusion_matrix(cm, class_names, cm_plot_path)

    metrics = {
        "metadata": {
            "model_name": "efficientnet_b0",
            "model_version": "1.0.0",
            "checkpoint_path": str(resolved_checkpoint),
            "test_split_path": str(resolved_split),
            "image_count": int(len(y_true)),
            "evaluation_time_seconds": round(total_time, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "multiclass_metrics": {
            "accuracy": round(accuracy, 4),
            "quadratic_weighted_kappa": round(qwk, 4),
            "macro_precision": round(float(macro_p), 4),
            "macro_recall": round(float(macro_r), 4),
            "macro_f1": round(float(macro_f1), 4),
            "weighted_precision": round(float(weighted_p), 4),
            "weighted_recall": round(float(weighted_r), 4),
            "weighted_f1": round(float(weighted_f1), 4),
        },
        "per_class_metrics": {
            f"grade_{c}": {
                "name": DR_GRADE_LABELS[c],
                "precision": round(float(per_class_p[c]), 4),
                "recall": round(float(per_class_r[c]), 4),
                "f1_score": round(float(per_class_f1[c]), 4),
                "support": int(per_class_support[c]),
            }
            for c in range(5)
        },
        "confusion_matrix": cm.tolist(),
        "referable_dr_screening_metrics": {
            "definition": "Referable DR defined as Grades 2, 3, 4 (ICDR Moderate, Severe, Proliferative)",
            "sensitivity_recall": round(ref_sensitivity, 4),
            "specificity": round(ref_specificity, 4),
            "accuracy": round(ref_accuracy, 4),
            "f1_score": round(ref_f1, 4),
            "contingency_table": {
                "true_positive": tp,
                "true_negative": tn,
                "false_positive": fp,
                "false_negative": fn,
            },
        },
    }

    metrics_json_path = resolved_output_dir / "metrics.json"
    with open(metrics_json_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[OK] Saved evaluation metrics JSON to {metrics_json_path}")

    return metrics


__all__ = [
    "to_numpy_1d",
    "validate_evaluation_inputs",
    "compute_classification_metrics",
    "map_external_dataset_labels",
    "verify_evaluation_assets",
    "plot_confusion_matrix",
    "run_test_evaluation",
    "EYERIS_NUM_CLASSES",
    "DEFAULT_SPLIT_PATH",
    "DEFAULT_IMG_DIR",
    "DEFAULT_OUTPUT_DIR",
]


if __name__ == "__main__":
    results = run_test_evaluation()
    print("\n" + "=" * 65)
    print("EVALUATION SUMMARY")
    print("=" * 65)
    print(f"Accuracy:                 {results['multiclass_metrics']['accuracy'] * 100:.2f}%")
    print(f"Quadratic Weighted Kappa: {results['multiclass_metrics']['quadratic_weighted_kappa']:.4f}")
    print(f"Macro F1-Score:           {results['multiclass_metrics']['macro_f1']:.4f}")
    print(f"Weighted F1-Score:        {results['multiclass_metrics']['weighted_f1']:.4f}")
    print(f"Referable Sensitivity:    {results['referable_dr_screening_metrics']['sensitivity_recall'] * 100:.2f}%")
    print(f"Referable Specificity:    {results['referable_dr_screening_metrics']['specificity'] * 100:.2f}%")
    print("=" * 65)
