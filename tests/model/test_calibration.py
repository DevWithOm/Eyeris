"""
Unit tests for confidence calibration, metrics (ECE, MCE, Brier score),
and Temperature Scaling module.
"""

from pathlib import Path
import shutil
import tempfile
import unittest
import numpy as np
import torch

from ai_models.explainability.calibration import (
    TemperatureScaler,
    compare_calibration,
    compute_brier_score,
    compute_ece,
    compute_mce,
    compute_nll,
    compute_reliability_diagram,
    evaluate_calibration,
    validate_logits_and_labels
)


def generate_synthetic_data(n_samples: int = 300, num_classes: int = 5, accuracy: float = 0.65, confidence_scale: float = 5.0, seed: int = 42):
    """
    Generates synthetic multiclass predictions simulating an overconfident deep neural network.
    Accuracy is roughly `accuracy` (e.g. 65%), but logits produce ~98% confidence.
    """
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, num_classes, size=n_samples)

    # Predictions match labels `accuracy` fraction of the time
    preds = labels.copy()
    n_wrong = int((1.0 - accuracy) * n_samples)
    wrong_idx = rng.choice(n_samples, size=n_wrong, replace=False)
    preds[wrong_idx] = (labels[wrong_idx] + rng.integers(1, num_classes, size=n_wrong)) % num_classes

    # Create overconfident logits
    logits = rng.normal(0.0, 0.2, size=(n_samples, num_classes))
    logits[np.arange(n_samples), preds] += confidence_scale

    return logits.astype(np.float32), labels.astype(np.int64)


class TestCalibration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.num_classes = 5

        # Synthetic validation and test sets (separate seeds, zero data leakage)
        self.val_logits, self.val_labels = generate_synthetic_data(
            n_samples=300, num_classes=5, accuracy=0.65, confidence_scale=5.0, seed=42
        )
        self.test_logits, self.test_labels = generate_synthetic_data(
            n_samples=200, num_classes=5, accuracy=0.65, confidence_scale=5.0, seed=123
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_validate_logits_and_labels_valid(self):
        logits_np, labels_np = validate_logits_and_labels(self.val_logits, self.val_labels)
        self.assertEqual(logits_np.shape, (300, self.num_classes))
        self.assertEqual(labels_np.shape, (300,))

    def test_validate_logits_and_labels_invalid_shapes(self):
        # 1D logits
        with self.assertRaises(ValueError):
            validate_logits_and_labels(np.array([1.0, 2.0]), np.array([1]))

        # Sample count mismatch
        with self.assertRaises(ValueError):
            validate_logits_and_labels(self.val_logits, self.val_labels[:10])

        # NaN values
        bad_logits = self.val_logits.copy()
        bad_logits[0, 0] = np.nan
        with self.assertRaises(ValueError):
            validate_logits_and_labels(bad_logits, self.val_labels)

        # Labels out of range
        bad_labels = self.val_labels.copy()
        bad_labels[0] = 99  # greater than num_classes - 1
        with self.assertRaises(ValueError):
            validate_logits_and_labels(self.val_logits, bad_labels)

    def test_compute_brier_score_perfect_and_uniform(self):
        # Perfect predictions: confidence 1.0 on true class
        perfect_probs = np.zeros((10, 5))
        labels = np.array([0, 1, 2, 3, 4, 0, 1, 2, 3, 4])
        perfect_probs[np.arange(10), labels] = 1.0
        self.assertAlmostEqual(compute_brier_score(perfect_probs, labels), 0.0, places=5)

        # Uniform predictions on 5 classes (0.2 each)
        uniform_probs = np.ones((10, 5)) * 0.2
        # (1 - 0.2)^2 + 4 * (0.2)^2 = 0.64 + 4 * 0.04 = 0.80
        self.assertAlmostEqual(compute_brier_score(uniform_probs, labels), 0.8, places=5)

    def test_compute_ece_perfect_predictions(self):
        perfect_probs = np.zeros((20, 5))
        labels = np.array([i % 5 for i in range(20)])
        perfect_probs[np.arange(20), labels] = 1.0
        ece = compute_ece(perfect_probs, labels, n_bins=10)
        self.assertAlmostEqual(ece, 0.0, places=5)

    def test_temperature_scaler_fit_and_calibrate(self):
        scaler = TemperatureScaler(initial_temperature=1.0)
        self.assertFalse(scaler.is_fitted)

        scaler.fit(self.val_logits, self.val_labels)
        self.assertTrue(scaler.is_fitted)

        # Since synthetic logits are overconfident (~65% accuracy with ~98% confidence),
        # optimal temperature T must be significantly > 1.0 to soften probabilities
        optimal_t = float(scaler.temperature.item())
        self.assertGreater(optimal_t, 1.2)

        # Calibrate logits
        cal_probs = scaler.predict_proba(self.val_logits)
        self.assertEqual(cal_probs.shape, self.val_logits.shape)

        # Check probabilities sum to 1.0
        row_sums = np.sum(cal_probs, axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=1e-5)

        # Crucial check: Temperature scaling MUST preserve top-1 predicted classes
        raw_preds = np.argmax(self.val_logits, axis=1)
        cal_preds = np.argmax(cal_probs, axis=1)
        np.testing.assert_array_equal(raw_preds, cal_preds)

    def test_temperature_scaler_save_and_load(self):
        scaler = TemperatureScaler(initial_temperature=1.85)
        scaler.is_fitted = True
        save_path = Path(self.test_dir) / "temperature.json"
        saved_file = scaler.save(save_path)
        self.assertTrue(Path(saved_file).is_file())

        loaded_scaler = TemperatureScaler.load(saved_file)
        self.assertAlmostEqual(float(loaded_scaler.temperature.item()), 1.85, places=4)
        self.assertTrue(loaded_scaler.is_fitted)

    def test_compare_calibration_improves_ece_without_leakage(self):
        comparison = compare_calibration(
            val_logits=self.val_logits,
            val_labels=self.val_labels,
            test_logits=self.test_logits,
            test_labels=self.test_labels,
            n_bins=10
        )

        self.assertEqual(comparison["status"], "success")
        uncal = comparison["uncalibrated"]
        cal = comparison["calibrated"]
        improvements = comparison["improvements"]

        # ECE should improve significantly (be lower after calibration)
        self.assertLess(cal["ece"], uncal["ece"])
        self.assertGreater(improvements["ece_reduction"], 0.1)

        # Brier score and NLL should improve
        self.assertLess(cal["brier_score"], uncal["brier_score"])
        self.assertLess(cal["nll"], uncal["nll"])

        # Accuracy must be completely unchanged
        self.assertEqual(uncal["accuracy"], cal["accuracy"])
        self.assertTrue(improvements["accuracy_preserved"])

    def test_reliability_diagram_structure(self):
        probs = np.ones((50, 5)) * 0.2
        labels = np.random.randint(0, 5, size=50)
        diagram = compute_reliability_diagram(probs, labels, n_bins=5)

        self.assertEqual(diagram["n_bins"], 5)
        self.assertEqual(len(diagram["bin_boundaries"]), 6)
        self.assertEqual(len(diagram["bin_accuracies"]), 5)
        self.assertEqual(len(diagram["bin_confidences"]), 5)
        self.assertEqual(len(diagram["bin_counts"]), 5)
        self.assertIn("ece", diagram)
        self.assertIn("mce", diagram)


if __name__ == "__main__":
    unittest.main()
