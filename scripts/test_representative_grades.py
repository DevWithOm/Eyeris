"""
Final End-to-End Inference Verification across All 5 DR Grades.

Selects verified APTOS test images covering Grade 0, Grade 1, Grade 2, Grade 3,
and Grade 4. Runs them through the public predict_grade() interface.
"""

import hashlib
from pathlib import Path
import sys

import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai_models.classification import predict_grade
from ai_models.common.labels import DR_GRADE_LABELS

# Verified paths
SPLIT_CSV = _PROJECT_ROOT / "data" / "manifests" / "test_split.csv"
IMG_DIR = Path(r"E:\DR_Classification_Project_Template\data\raw\aptos\train_images")


def run_test():
    print("=" * 75)
    print("MEMBER 1: 5-GRADE REPRESENTATIVE INFERENCE TEST")
    print("=" * 75)

    df_split = pd.read_csv(SPLIT_CSV)

    # Selected representative samples from held-out test set
    test_cases = [
        ("d9ad2a0ec026", 0),  # No DR
        ("ca7140ecf389", 1),  # Mild
        ("89ee1fa16f90", 2),  # Moderate
        ("070f67572d03", 3),  # Severe
        ("8eeac97f02f0", 4),  # Proliferative DR
    ]

    results = []

    for id_code, expected_gt in test_cases:
        img_file = IMG_DIR / f"{id_code}.png"
        if not img_file.exists():
            raise FileNotFoundError(f"Test image not found: {img_file}")

        # Confirm GT from test split
        gt_entry = df_split[df_split["id_code"] == id_code]
        assert not gt_entry.empty, f"ID {id_code} not in split!"
        actual_gt = int(gt_entry.iloc[0]["diagnosis"])
        assert actual_gt == expected_gt, f"GT mismatch for {id_code}!"

        # SHA-256 before inference
        sha_before = hashlib.sha256(img_file.read_bytes()).hexdigest()

        # Public API call
        res = predict_grade(str(img_file))

        # SHA-256 after inference
        sha_after = hashlib.sha256(img_file.read_bytes()).hexdigest()
        assert sha_before == sha_after, f"Image {img_file} was modified during inference!"

        pred_grade = res["predicted_grade"]
        grade_name = res["grade_name"]
        raw_conf = res["raw_confidence"]
        probs = res["probabilities"]
        prob_sum = sum(probs)
        is_match = (pred_grade == actual_gt)

        print(f"\n--- Sample: {id_code}.png ---")
        print(f"  File Path:           {img_file}")
        print(f"  Ground-Truth Grade:  Grade {actual_gt} ({DR_GRADE_LABELS[actual_gt]})")
        print(f"  Predicted Grade:     Grade {pred_grade} ({grade_name})")
        print(f"  Ground-Truth Match:  {'YES (Correct)' if is_match else 'NO (Misclassified)'}")
        print(f"  Raw Confidence:      {raw_conf:.6f} ({raw_conf * 100:.2f}%)")
        print(f"  Probability Sum:     {prob_sum:.8f} (Sum ~ 1.0: {abs(prob_sum - 1.0) < 1e-5})")
        print(f"  File Integrity:      UNCHANGED (SHA-256: {sha_before[:16]}...)")
        print("  Class Probabilities:")
        for c in range(5):
            marker = " <-- PREDICTED" if c == pred_grade else ""
            gt_tag = " [ACTUAL GT]" if c == actual_gt else ""
            print(f"    Class {c} ({DR_GRADE_LABELS[c]:17s}): {probs[c]:.6f}{marker}{gt_tag}")

        results.append({
            "id_code": id_code,
            "gt": actual_gt,
            "pred": pred_grade,
            "match": is_match,
            "raw_conf": raw_conf,
            "probs": probs,
        })

    # Also test an edge case / misclassified sample to demonstrate honest failure reporting
    print("\n" + "=" * 75)
    print("ADDITIONAL AUDIT: BOUNDARY / FAILURE CASE ANALYSIS")
    print("=" * 75)
    boundary_cases = [
        ("cfd1bd0fcbb4", 1),  # True Grade 1 (Mild) that gets predicted as Grade 0 (No DR)
        ("3ac3fbfca7d4", 4),  # True Grade 4 (Proliferative) that gets predicted as Grade 3 (Severe)
    ]
    for b_id, b_gt in boundary_cases:
        b_file = IMG_DIR / f"{b_id}.png"
        b_res = predict_grade(str(b_file))
        b_pred = b_res["predicted_grade"]
        print(f"\nBoundary Sample: {b_id}.png")
        print(f"  Actual Ground Truth: Grade {b_gt} ({DR_GRADE_LABELS[b_gt]})")
        print(f"  Model Prediction:    Grade {b_pred} ({b_res['grade_name']})")
        print(f"  Raw Confidence:      {b_res['raw_confidence']:.4f}")
        print(f"  Matches Ground Truth: {b_pred == b_gt}")
        print("  Probabilities:       " + ", ".join(f"C{i}: {p:.3f}" for i, p in enumerate(b_res["probabilities"])))

    print("\n" + "=" * 75)
    print("ALL END-TO-END TESTS COMPLETED SUCCESSFULLY.")
    print("=" * 75)


if __name__ == "__main__":
    run_test()
