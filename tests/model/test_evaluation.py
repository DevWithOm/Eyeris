"""
Unit tests for classification evaluation metrics, external dataset mappings,
and explanation/Grad-CAM validation routines.
"""

import unittest
import numpy as np
import torch

from ai_models.classification.evaluate import (
    compute_classification_metrics,
    map_external_dataset_labels,
    validate_evaluation_inputs
)
from ai_models.explainability.evaluate_explanations import (
    compute_attribution_mass,
    compute_explanation_iou,
    evaluate_explanation_batch,
    evaluate_pointing_game,
    validate_heatmap_and_mask
)


class TestClassificationEvaluation(unittest.TestCase):
    def test_classification_metrics_perfect(self):
        y_true = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]
        y_pred = [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]

        res = compute_classification_metrics(y_true, y_pred)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["sample_count"], 10)

        multi = res["multiclass"]
        self.assertAlmostEqual(multi["overall_accuracy"], 1.0)
        self.assertAlmostEqual(multi["macro_precision"], 1.0)
        self.assertAlmostEqual(multi["macro_recall"], 1.0)
        self.assertAlmostEqual(multi["macro_f1"], 1.0)
        self.assertAlmostEqual(multi["weighted_f1"], 1.0)
        self.assertAlmostEqual(multi["quadratic_weighted_kappa"], 1.0)

        # 5x5 confusion matrix diagonal
        cm = np.array(multi["confusion_matrix_5class"])
        self.assertEqual(cm.shape, (5, 5))
        np.testing.assert_array_equal(np.diag(cm), [2, 2, 2, 2, 2])

        # Clinical referable metrics
        ref = res["referable_dr"]
        self.assertAlmostEqual(ref["sensitivity"], 1.0)
        self.assertAlmostEqual(ref["specificity"], 1.0)
        self.assertAlmostEqual(ref["precision_ppv"], 1.0)
        self.assertAlmostEqual(ref["npv"], 1.0)
        self.assertAlmostEqual(ref["binary_accuracy"], 1.0)

    def test_classification_metrics_missing_classes(self):
        # Dataset contains only grades 0, 1, 2; grades 3 and 4 are missing
        y_true = [0, 1, 2, 0, 1, 2]
        y_pred = [0, 1, 1, 0, 1, 2]

        res = compute_classification_metrics(y_true, y_pred)
        multi = res["multiclass"]

        # Confusion matrix is still full 5x5
        cm = np.array(multi["confusion_matrix_5class"])
        self.assertEqual(cm.shape, (5, 5))

        # Check per-class metrics handle zero support
        per_class = multi["per_class"]
        self.assertEqual(per_class["Severe"]["support"], 0)
        self.assertIsNone(per_class["Severe"]["recall"])
        self.assertIsNone(per_class["Severe"]["f1_score"])

    def test_classification_metrics_no_positive_referable_cases(self):
        # Only Non-Referable cases (Grades 0 and 1)
        y_true = [0, 0, 1, 1]
        y_pred = [0, 0, 0, 1]

        res = compute_classification_metrics(y_true, y_pred, referable_threshold=2)
        ref = res["referable_dr"]

        # Sensitivity is undefined when positive cases = 0; must be None, not 0.0
        self.assertIsNone(ref["sensitivity"])
        self.assertAlmostEqual(ref["specificity"], 1.0)
        self.assertAlmostEqual(ref["binary_accuracy"], 1.0)

    def test_quadratic_weighted_kappa_penalty(self):
        # Construct mild off‑by‑1 scenario and severe off‑by‑4 scenario with matching lengths.
        y_true_mild = np.array([0, 0, 0, 0, 0, 1, 2, 3, 4])
        y_pred_mild = np.array([1, 1, 1, 1, 1, 0, 1, 2, 3])
        y_true_severe = np.array([0, 0, 0, 0, 0, 4, 4, 4, 4, 4])
        y_pred_severe = np.array([4, 4, 4, 4, 4, 0, 0, 0, 0, 0])
        res_mild = compute_classification_metrics(y_true_mild.tolist(), y_pred_mild.tolist())
        res_poor = compute_classification_metrics(y_true_severe.tolist(), y_pred_severe.tolist())
        self.assertGreater(
            res_mild["multiclass"]["quadratic_weighted_kappa"],
            res_poor["multiclass"]["quadratic_weighted_kappa"]
        )

    def test_classification_metrics_invalid_inputs(self):
        # Mismatched lengths
        with self.assertRaises(ValueError):
            compute_classification_metrics([0, 1, 2], [0, 1])

        # Empty array
        with self.assertRaises(ValueError):
            compute_classification_metrics([], [])

        # NaN values
        with self.assertRaises(ValueError):
            compute_classification_metrics([0, np.nan], [0, 1])

        # Out-of-bounds labels (grade 5)
        with self.assertRaises(ValueError):
            compute_classification_metrics([0, 5], [0, 1])

    def test_map_external_dataset_labels_aptos_and_idrid(self):
        labels = [0, 1, 2, 3, 4]
        mapped_aptos = map_external_dataset_labels(labels, dataset_name="aptos_2019")
        np.testing.assert_array_equal(mapped_aptos, labels)

        mapped_idrid = map_external_dataset_labels(labels, dataset_name="idrid")
        np.testing.assert_array_equal(mapped_idrid, labels)

    def test_map_external_dataset_labels_messidor_2(self):
        # Messidor-2 referable binary mapping
        labels = [0, 1, 2, 3]
        mapped = map_external_dataset_labels(labels, dataset_name="messidor_2_referable")
        np.testing.assert_array_equal(mapped, [0, 0, 1, 1])

        # Calling 'messidor_2' without explicit mapping raises informative error
        with self.assertRaises(ValueError) as ctx:
            map_external_dataset_labels(labels, dataset_name="messidor_2")
        self.assertIn("cannot be unambiguously mapped", str(ctx.exception))

        # Explicit custom mapping succeeds
        custom_map = {0: 0, 1: 1, 2: 2, 3: 4}
        mapped_custom = map_external_dataset_labels(labels, dataset_name="messidor_2", label_mapping=custom_map)
        np.testing.assert_array_equal(mapped_custom, [0, 1, 2, 4])

    def test_map_external_dataset_labels_unsupported(self):
        with self.assertRaises(ValueError):
            map_external_dataset_labels([0, 1], dataset_name="unknown_dataset_xyz")


class TestExplanationEvaluation(unittest.TestCase):
    def setUp(self):
        self.height, self.width = 50, 50

        # Create lesion mask with positive lesion in [10:25, 10:25]
        self.lesion_mask = np.zeros((self.height, self.width), dtype=np.float32)
        self.lesion_mask[10:25, 10:25] = 1.0

        # Heatmap 1: Peak activation inside lesion at (15, 15)
        self.heatmap_hit = np.zeros((self.height, self.width), dtype=np.float32)
        self.heatmap_hit[10:25, 10:25] = 0.8
        self.heatmap_hit[15, 15] = 1.0

        # Heatmap 2: Peak activation outside lesion at (40, 40)
        self.heatmap_miss = np.zeros((self.height, self.width), dtype=np.float32)
        self.heatmap_miss[35:45, 35:45] = 0.8
        self.heatmap_miss[40, 40] = 1.0

    def test_pointing_game_hit_and_miss(self):
        # Hit case
        res_hit = evaluate_pointing_game(self.heatmap_hit, self.lesion_mask)
        self.assertEqual(res_hit["status"], "evaluated")
        self.assertTrue(res_hit["hit"])
        self.assertEqual(res_hit["max_point"], (15, 15))

        # Miss case
        res_miss = evaluate_pointing_game(self.heatmap_miss, self.lesion_mask)
        self.assertEqual(res_miss["status"], "evaluated")
        self.assertFalse(res_miss["hit"])
        self.assertEqual(res_miss["max_point"], (40, 40))

    def test_pointing_game_empty_mask_and_zero_energy(self):
        empty_mask = np.zeros((self.height, self.width), dtype=np.float32)
        res_empty = evaluate_pointing_game(self.heatmap_hit, empty_mask)
        self.assertEqual(res_empty["status"], "empty_mask")
        self.assertIsNone(res_empty["hit"])

        zero_hm = np.zeros((self.height, self.width), dtype=np.float32)
        res_zero = evaluate_pointing_game(zero_hm, self.lesion_mask)
        self.assertEqual(res_zero["status"], "zero_energy_heatmap")
        self.assertFalse(res_zero["hit"])

    def test_compute_attribution_mass(self):
        # Heatmap completely inside lesion
        res_perfect = compute_attribution_mass(self.heatmap_hit, self.lesion_mask)
        self.assertEqual(res_perfect["status"], "evaluated")
        self.assertAlmostEqual(res_perfect["attribution_mass"], 1.0)

        # Heatmap completely outside lesion
        res_zero = compute_attribution_mass(self.heatmap_miss, self.lesion_mask)
        self.assertEqual(res_zero["status"], "evaluated")
        self.assertAlmostEqual(res_zero["attribution_mass"], 0.0)

    def test_compute_explanation_iou_and_dice(self):
        # Perfect overlap
        mask_square = np.zeros((50, 50), dtype=np.float32)
        mask_square[10:20, 10:20] = 1.0
        hm_square = np.zeros((50, 50), dtype=np.float32)
        hm_square[10:20, 10:20] = 0.9  # above threshold=0.5

        res_perf = compute_explanation_iou(hm_square, mask_square, threshold=0.5)
        self.assertEqual(res_perf["status"], "evaluated")
        self.assertAlmostEqual(res_perf["iou"], 1.0)
        self.assertAlmostEqual(res_perf["dice"], 1.0)

        # Disjoint overlap
        hm_disjoint = np.zeros((50, 50), dtype=np.float32)
        hm_disjoint[30:40, 30:40] = 0.9

        res_disjoint = compute_explanation_iou(hm_disjoint, mask_square, threshold=0.5)
        self.assertEqual(res_disjoint["status"], "evaluated")
        self.assertAlmostEqual(res_disjoint["iou"], 0.0)
        self.assertAlmostEqual(res_disjoint["dice"], 0.0)

        # Both empty
        empty_square = np.zeros((50, 50), dtype=np.float32)
        res_empty = compute_explanation_iou(empty_square, empty_square, threshold=0.5)
        self.assertEqual(res_empty["status"], "empty_union")
        self.assertIsNone(res_empty["iou"])
        self.assertIsNone(res_empty["dice"])

    def test_evaluate_explanation_batch_with_missing_masks(self):
        heatmaps = [self.heatmap_hit, self.heatmap_miss, self.heatmap_hit]
        # First has lesion, second has None (missing annotation), third has empty mask (no lesion)
        masks = [self.lesion_mask, None, np.zeros((self.height, self.width), dtype=np.float32)]

        batch_res = evaluate_explanation_batch(heatmaps, masks, threshold=0.5)
        self.assertEqual(batch_res["status"], "success")

        counts = batch_res["counts"]
        self.assertEqual(counts["total_cases"], 3)
        self.assertEqual(counts["evaluated_cases"], 2)
        self.assertEqual(counts["skipped_missing_masks"], 1)
        self.assertEqual(counts["empty_mask_cases"], 1)
        self.assertEqual(counts["pointing_evaluable_cases"], 1)

        # Only 1 evaluable case (case 0 was a hit)
        self.assertAlmostEqual(batch_res["aggregate_metrics"]["pointing_game_accuracy"], 1.0)

    def test_dimension_mismatch_raises_error(self):
        small_mask = np.zeros((20, 20), dtype=np.float32)
        with self.assertRaises(ValueError):
            evaluate_pointing_game(self.heatmap_hit, small_mask)


if __name__ == "__main__":
    unittest.main()

