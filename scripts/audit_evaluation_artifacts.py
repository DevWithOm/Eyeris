"""
Evaluation Artifact Audit Script.

Audits:
1. Opens and validates artifacts/evaluation/metrics.json.
2. Opens and validates artifacts/evaluation/classification_report.csv.
3. Inspects artifacts/evaluation/test_predictions.csv.
4. Verifies test_predictions.csv contains exactly 550 unique test images.
5. Recalculates accuracy, macro F1, weighted F1, QWK, and referable sensitivity/specificity
   directly from the ground-truth and prediction columns.
6. Verifies that the confusion matrix reconstructed from test_predictions.csv matches reported values.
7. Confirms that no training or validation images appear in the test prediction file.
8. Confirms that the checkpoint used is artifacts/model_weights/best_model.pth.
"""

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_audit() -> bool:
    print("=" * 65)
    print("MEMBER 1: EVALUATION ARTIFACT AUDIT")
    print("=" * 65)

    discrepancies = []

    # 1. Open metrics.json
    metrics_path = _PROJECT_ROOT / "artifacts" / "evaluation" / "metrics.json"
    if not metrics_path.exists():
        print(f"[FAIL] metrics.json not found at {metrics_path}")
        return False
    with open(metrics_path, "r") as f:
        metrics = json.load(f)
    print(f"1. [PASS] Loaded metrics.json ({metrics_path.stat().st_size} bytes)")

    # 2. Open classification_report.csv
    report_path = _PROJECT_ROOT / "artifacts" / "evaluation" / "classification_report.csv"
    if not report_path.exists():
        print(f"[FAIL] classification_report.csv not found at {report_path}")
        return False
    df_report = pd.read_csv(report_path)
    print(f"2. [PASS] Loaded classification_report.csv ({len(df_report)} rows, columns: {list(df_report.columns)})")

    # 3. Inspect test_predictions.csv
    preds_path = _PROJECT_ROOT / "artifacts" / "evaluation" / "test_predictions.csv"
    if not preds_path.exists():
        print(f"[FAIL] test_predictions.csv not found at {preds_path}")
        return False
    df_preds = pd.read_csv(preds_path)
    print(f"3. [PASS] Loaded test_predictions.csv ({len(df_preds)} rows, columns: {list(df_preds.columns)})")

    # 4. Verify unique count is exactly 550
    total_rows = len(df_preds)
    unique_ids = int(df_preds["id_code"].nunique())
    print(f"\n4. Image Count Audit:")
    print(f"   Total rows:         {total_rows}")
    print(f"   Unique image IDs:   {unique_ids}")
    if total_rows != 550 or unique_ids != 550:
        err = f"Expected exactly 550 unique images, found {total_rows} rows and {unique_ids} unique IDs."
        print(f"   [FAIL] {err}")
        discrepancies.append(err)
    else:
        print("   [PASS] test_predictions.csv contains exactly 550 unique test images.")

    # 5. Recalculate metrics directly from columns
    y_true = df_preds["true_grade"].to_numpy()
    y_pred = df_preds["predicted_grade"].to_numpy()

    recalc_acc = float(accuracy_score(y_true, y_pred))
    recalc_macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    recalc_weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    recalc_qwk = float(cohen_kappa_score(y_true, y_pred, weights="quadratic"))

    # Referable DR metrics
    y_true_ref = (y_true >= 2).astype(int)
    y_pred_ref = (y_pred >= 2).astype(int)
    tp = int(np.sum((y_true_ref == 1) & (y_pred_ref == 1)))
    tn = int(np.sum((y_true_ref == 0) & (y_pred_ref == 0)))
    fp = int(np.sum((y_true_ref == 0) & (y_pred_ref == 1)))
    fn = int(np.sum((y_true_ref == 1) & (y_pred_ref == 0)))
    recalc_sens = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    recalc_spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    reported_acc = metrics["multiclass_metrics"]["accuracy"]
    reported_macro_f1 = metrics["multiclass_metrics"]["macro_f1"]
    reported_weighted_f1 = metrics["multiclass_metrics"]["weighted_f1"]
    reported_qwk = metrics["multiclass_metrics"]["quadratic_weighted_kappa"]
    reported_sens = metrics["referable_dr_screening_metrics"]["sensitivity_recall"]
    reported_spec = metrics["referable_dr_screening_metrics"]["specificity"]

    print(f"\n5. Recalculated vs Reported Metric Audit:")
    metric_comparisons = [
        ("Accuracy", recalc_acc, reported_acc),
        ("Macro F1", recalc_macro_f1, reported_macro_f1),
        ("Weighted F1", recalc_weighted_f1, reported_weighted_f1),
        ("QWK", recalc_qwk, reported_qwk),
        ("Sensitivity", recalc_sens, reported_sens),
        ("Specificity", recalc_spec, reported_spec),
    ]

    for name, recalc, reported in metric_comparisons:
        diff = abs(recalc - reported)
        is_match = diff < 1e-4
        status = "[MATCH]" if is_match else "[MISMATCH]"
        print(f"   {name:15s}: Recalc={recalc:.4f} | Reported={reported:.4f} | Diff={diff:.6f} {status}")
        if not is_match:
            discrepancies.append(f"{name} mismatch: Recalc={recalc} vs Reported={reported}")

    # 6. Reconstruct Confusion Matrix
    recalc_cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3, 4])
    reported_cm = np.array(metrics["confusion_matrix"])
    cm_matches = np.array_equal(recalc_cm, reported_cm)
    print(f"\n6. Confusion Matrix Verification:")
    print(f"   Reconstructed matrix equals reported matrix: {cm_matches}")
    if not cm_matches:
        discrepancies.append("Confusion matrix mismatch between test_predictions.csv and metrics.json")
    else:
        print("   [PASS] Confusion matrix perfectly verified.")

    # 7. Check Data Leakage against Train and Validation Splits
    train_path = Path(r"E:\Minor Project\DR_Classification_Project_Template\data\splits\train_split.csv")
    val_path = Path(r"E:\Minor Project\DR_Classification_Project_Template\data\splits\val_split.csv")
    
    if not train_path.exists() or not val_path.exists():
        err = f"Train/Val split files not found at {train_path} or {val_path}"
        print(f"   [FAIL] {err}")
        discrepancies.append(err)
    else:
        df_train = pd.read_csv(train_path)
        df_val = pd.read_csv(val_path)

        test_ids = set(df_preds["id_code"])
        train_ids = set(df_train["id_code"])
        val_ids = set(df_val["id_code"])

        train_overlap = test_ids.intersection(train_ids)
        val_overlap = test_ids.intersection(val_ids)

        print(f"\n7. Data Leakage & Split Independence Audit:")
        print(f"   Training images count:   {len(train_ids)}")
        print(f"   Validation images count: {len(val_ids)}")
        print(f"   Test images count:       {len(test_ids)}")
        print(f"   Test ∩ Train overlap:    {len(train_overlap)}")
        print(f"   Test ∩ Val overlap:      {len(val_overlap)}")

        if len(train_overlap) > 0:
            err = f"Data leakage detected! {len(train_overlap)} test images are in training set."
            print(f"   [FAIL] {err}")
            discrepancies.append(err)
        else:
            print("   [PASS] 0 overlap between Test set and Training set.")

        if len(val_overlap) > 0:
            err = f"Data leakage detected! {len(val_overlap)} test images are in validation set."
            print(f"   [FAIL] {err}")
            discrepancies.append(err)
        else:
            print("   [PASS] 0 overlap between Test set and Validation set.")

    # 8. Checkpoint Path Verification
    reported_ckpt_str = metrics["metadata"]["checkpoint_path"]
    reported_ckpt = Path(reported_ckpt_str).resolve()
    target_ckpt = (_PROJECT_ROOT / "artifacts" / "model_weights" / "best_model.pth").resolve()

    print(f"\n8. Checkpoint Origin Audit:")
    print(f"   Reported checkpoint:  {reported_ckpt}")
    print(f"   Target checkpoint:    {target_ckpt}")
    print(f"   Paths resolve equal:  {reported_ckpt == target_ckpt}")
    print(f"   File exists on disk:  {reported_ckpt.exists()}")
    if reported_ckpt.exists():
        size_mb = reported_ckpt.stat().st_size / (1024 * 1024)
        print(f"   Checkpoint file size: {size_mb:.2f} MB")

    if reported_ckpt != target_ckpt:
        err = f"Checkpoint path mismatch: {reported_ckpt} != {target_ckpt}"
        print(f"   [FAIL] {err}")
        discrepancies.append(err)
    else:
        print("   [PASS] Confirmed checkpoint used is artifacts/model_weights/best_model.pth.")

    print("\n" + "=" * 65)
    if discrepancies:
        print(f"AUDIT COMPLETED: {len(discrepancies)} DISCREPANCY/DISCREPANCIES FOUND:")
        for d in discrepancies:
            print(f"  - {d}")
        return False
    else:
        print("AUDIT COMPLETED: ZERO DISCREPANCIES FOUND. ALL VERIFICATIONS PASSED.")
        print("=" * 65)
        return True


if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
