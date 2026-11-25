"""
Unit tests for predictive confidence extraction, Shannon entropy,
prediction margins, and uncertainty estimation.
"""

import unittest
import numpy as np
import torch

from ai_models.explainability.confidence import (
    compute_entropy,
    compute_prediction_margin,
    compute_top_confidence,
    estimate_batch_uncertainty,
    estimate_case_uncertainty,
    validate_probabilities
)


class TestConfidenceAndUncertainty(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        torch.manual_seed(42)

        # 5-grade diabetic retinopathy setups
        self.num_classes = 5

        # 1. Decisive / Highly Certain prediction (e.g. clear No DR)
        self.certain_probs = np.array([0.95, 0.03, 0.01, 0.01, 0.0], dtype=np.float32)

        # 2. Ambivalent / High Uncertainty prediction (e.g. boundary between Mild and Moderate DR)
        self.ambivalent_probs = np.array([0.05, 0.48, 0.45, 0.02, 0.0], dtype=np.float32)

        # 3. Maximum Entropy / Uniformly Ambiguous prediction (model completely uncertain)
        self.uniform_probs = np.array([0.2, 0.2, 0.2, 0.2, 0.2], dtype=np.float32)

        # 4. Perfectly Certain prediction
        self.perfect_probs = np.array([1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    def test_validate_probabilities_formats(self):
        # 1D numpy array
        p1 = validate_probabilities(self.certain_probs)
        self.assertEqual(p1.shape, (1, 5))

        # 2D numpy array
        batch = np.vstack([self.certain_probs, self.ambivalent_probs])
        p2 = validate_probabilities(batch)
        self.assertEqual(p2.shape, (2, 5))

        # PyTorch Tensor
        tensor = torch.tensor(self.certain_probs)
        p3 = validate_probabilities(tensor)
        self.assertEqual(p3.shape, (1, 5))

        # Python list
        p4 = validate_probabilities([0.2, 0.2, 0.2, 0.2, 0.2])
        self.assertEqual(p4.shape, (1, 5))

    def test_validate_probabilities_invalid_inputs(self):
        # Empty array
        with self.assertRaises(ValueError):
            validate_probabilities([])

        # Negative probabilities
        with self.assertRaises(ValueError):
            validate_probabilities([0.5, -0.1, 0.4, 0.2, 0.0])

        # NaN values
        with self.assertRaises(ValueError):
            validate_probabilities([0.5, np.nan, 0.3, 0.1, 0.1])

        # Infinite values
        with self.assertRaises(ValueError):
            validate_probabilities([0.5, np.inf, 0.3, 0.1, 0.1])

        # Row sum far from 1.0
        with self.assertRaises(ValueError):
            validate_probabilities([0.1, 0.1, 0.1, 0.1, 0.1])  # sums to 0.5

        # Degenerate single class
        with self.assertRaises(ValueError):
            validate_probabilities([1.0])

        # 3D tensor
        with self.assertRaises(ValueError):
            validate_probabilities(np.zeros((2, 2, 2)))

    def test_compute_entropy_bounds(self):
        # Perfect certainty -> Normalized entropy must be 0.0
        h_perfect = compute_entropy(self.perfect_probs, normalize=True)
        self.assertAlmostEqual(float(h_perfect[0]), 0.0, places=5)

        # Uniform uncertainty -> Normalized entropy must be 1.0
        h_uniform = compute_entropy(self.uniform_probs, normalize=True)
        self.assertAlmostEqual(float(h_uniform[0]), 1.0, places=5)

        # Certain case has lower entropy than ambivalent case
        h_certain = float(compute_entropy(self.certain_probs, normalize=True)[0])
        h_ambivalent = float(compute_entropy(self.ambivalent_probs, normalize=True)[0])

        self.assertLess(h_certain, h_ambivalent)
        self.assertGreater(h_certain, 0.0)
        self.assertLess(h_ambivalent, 1.0)

    def test_compute_top_confidence(self):
        conf, pred = compute_top_confidence(self.certain_probs)
        self.assertAlmostEqual(float(conf[0]), 0.95, places=4)
        self.assertEqual(int(pred[0]), 0)

        conf_amb, pred_amb = compute_top_confidence(self.ambivalent_probs)
        self.assertAlmostEqual(float(conf_amb[0]), 0.48, places=4)
        self.assertEqual(int(pred_amb[0]), 1)

    def test_compute_prediction_margin(self):
        # Certain case: 0.95 vs 0.03 -> margin = 0.92
        margin_c, uncert_c = compute_prediction_margin(self.certain_probs)
        self.assertAlmostEqual(float(margin_c[0]), 0.92, places=4)
        self.assertAlmostEqual(float(uncert_c[0]), 0.08, places=4)

        # Ambivalent case: 0.48 vs 0.45 -> margin = 0.03 (very narrow margin)
        margin_a, uncert_a = compute_prediction_margin(self.ambivalent_probs)
        self.assertAlmostEqual(float(margin_a[0]), 0.03, places=4)
        self.assertAlmostEqual(float(uncert_a[0]), 0.97, places=4)

        # Uniform case: 0.2 vs 0.2 -> margin = 0.0
        margin_u, uncert_u = compute_prediction_margin(self.uniform_probs)
        self.assertAlmostEqual(float(margin_u[0]), 0.0, places=4)
        self.assertAlmostEqual(float(uncert_u[0]), 1.0, places=4)

    def test_estimate_case_uncertainty_structure_and_threshold(self):
        # Case without threshold
        res = estimate_case_uncertainty(self.certain_probs)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["predicted_class"], 0)
        self.assertEqual(res["predicted_class_label"], "No DR")
        self.assertAlmostEqual(res["confidence"], 0.95, places=4)
        self.assertIn("normalized_entropy", res["uncertainty"])
        self.assertIn("prediction_margin", res["uncertainty"])
        self.assertIsNone(res["policy"]["flagged_for_human_review"])

        # Check top 2 candidates
        top_2 = res["top_2_candidates"]
        self.assertEqual(len(top_2), 2)
        self.assertEqual(top_2[0]["class_index"], 0)
        self.assertEqual(top_2[1]["class_index"], 1)

        # Case with threshold = 0.5
        threshold = 0.5
        # Certain case should NOT be flagged
        res_c = estimate_case_uncertainty(self.certain_probs, uncertainty_threshold=threshold)
        self.assertFalse(res_c["policy"]["flagged_for_human_review"])

        # Ambivalent case SHOULD be flagged
        res_a = estimate_case_uncertainty(self.ambivalent_probs, uncertainty_threshold=threshold)
        self.assertTrue(res_a["policy"]["flagged_for_human_review"])

        # Invalid threshold outside [0, 1]
        with self.assertRaises(ValueError):
            estimate_case_uncertainty(self.certain_probs, uncertainty_threshold=1.5)

    def test_estimate_case_uncertainty_with_calibrated_probabilities(self):
        raw_probs = np.array([0.98, 0.01, 0.01, 0.0, 0.0], dtype=np.float32)
        # Calibrated with T > 1.0 (softer confidence)
        cal_probs = np.array([0.80, 0.08, 0.06, 0.03, 0.03], dtype=np.float32)

        res = estimate_case_uncertainty(
            probs=raw_probs,
            calibrated_probs=cal_probs,
            is_calibrated=False
        )

        self.assertFalse(res["is_calibrated"])
        self.assertIn("calibrated_comparison", res)
        cal_comp = res["calibrated_comparison"]
        self.assertAlmostEqual(cal_comp["calibrated_confidence"], 0.80, places=4)
        self.assertGreater(cal_comp["calibrated_normalized_entropy"], res["uncertainty"]["normalized_entropy"])

    def test_estimate_batch_uncertainty(self):
        batch = np.vstack([self.certain_probs, self.ambivalent_probs, self.uniform_probs])
        res = estimate_batch_uncertainty(batch, uncertainty_threshold=0.5)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["sample_count"], 3)
        self.assertEqual(len(res["predicted_classes"]), 3)
        self.assertEqual(len(res["confidences"]), 3)
        self.assertEqual(len(res["normalized_entropies"]), 3)

        # Flagged mask should be [False, True, True]
        self.assertEqual(res["flagged_for_human_review"], [False, True, True])

        summary = res["batch_summary"]
        self.assertIn("mean_confidence", summary)
        self.assertIn("mean_normalized_entropy", summary)
        self.assertAlmostEqual(summary["percent_uncertain"], 66.6666, places=1)


if __name__ == "__main__":
    unittest.main()

