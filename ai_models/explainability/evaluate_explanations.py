"""
Explanation validation and spatial localization metrics for Diabetic Retinopathy screening.

Evaluates Grad-CAM visual heatmaps against ground-truth retinal lesion annotations (e.g. from IDRiD):
- Pointing Game Accuracy (peak saliency alignment)
- Attribution Mass inside Lesions (energy fraction within mask)
- Binarized Heatmap Intersection-over-Union (IoU) and Dice Coefficient
- Batch evaluation handling missing annotations, empty masks, and zero-energy heatmaps
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch

try:
    from ai_models.explainability.visualization import project_heatmap_to_original
except ImportError:
    project_heatmap_to_original = None


def to_2d_numpy(arr: Union[torch.Tensor, np.ndarray, List], name: str = "array") -> np.ndarray:
    """Safely converts input tensor, list, or array to a 2D float32 NumPy array."""
    if isinstance(arr, torch.Tensor):
        arr_np = arr.detach().cpu().numpy().astype(np.float32)
    else:
        arr_np = np.asarray(arr, dtype=np.float32)

    if arr_np.ndim != 2:
        raise ValueError(f"Expected 2D array for {name}, got shape {arr_np.shape}")

    if np.isnan(arr_np).any() or np.isinf(arr_np).any():
        raise ValueError(f"{name} contains NaN or Infinite values.")

    return arr_np


def validate_heatmap_and_mask(
    heatmap: Union[torch.Tensor, np.ndarray],
    lesion_mask: Union[torch.Tensor, np.ndarray]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validates dimensions and values for heatmap and lesion mask.
    """
    hm_np = to_2d_numpy(heatmap, name="heatmap")
    mask_np = to_2d_numpy(lesion_mask, name="lesion_mask")

    if hm_np.shape != mask_np.shape:
        raise ValueError(
            f"Shape mismatch: heatmap has shape {hm_np.shape}, but lesion_mask has shape {mask_np.shape}. "
            "Use project_heatmap_to_original() to align cropped heatmaps before evaluation."
        )

    if (hm_np < 0.0).any():
        raise ValueError("Heatmap values must be non-negative.")

    return hm_np, mask_np


def evaluate_pointing_game(
    heatmap: Union[torch.Tensor, np.ndarray],
    lesion_mask: Union[torch.Tensor, np.ndarray]
) -> Dict[str, Any]:
    """
    Evaluates Pointing Game accuracy: checks whether the maximum saliency point of the
    Grad-CAM heatmap falls inside an annotated lesion area.

    Args:
        heatmap: 2D float array with values in [0.0, 1.0].
        lesion_mask: 2D array where values > 0 indicate lesion tissue.

    Returns:
        Dict containing:
            - hit: True if peak falls inside lesion, False if outside, None if no lesions exist
            - max_point: (x, y) coordinates of peak activation
            - status: "evaluated", "empty_mask", or "zero_energy_heatmap"
    """
    hm_np, mask_np = validate_heatmap_and_mask(heatmap, lesion_mask)

    lesion_pixels = int(np.sum(mask_np > 0))
    if lesion_pixels == 0:
        return {
            "hit": None,
            "status": "empty_mask",
            "reason": "Ground-truth mask contains no positive lesion pixels.",
            "max_point": None,
            "max_value": float(np.max(hm_np)),
            "lesion_pixel_count": 0
        }

    max_val = float(np.max(hm_np))
    if max_val <= 1e-12:
        return {
            "hit": False,
            "status": "zero_energy_heatmap",
            "reason": "Heatmap contains zero energy across all pixels.",
            "max_point": None,
            "max_value": 0.0,
            "lesion_pixel_count": lesion_pixels
        }

    # Find coordinates of maximum saliency (row y, col x)
    y_max, x_max = np.unravel_index(np.argmax(hm_np), hm_np.shape)
    hit = bool(mask_np[y_max, x_max] > 0)

    return {
        "hit": hit,
        "status": "evaluated",
        "max_point": (int(x_max), int(y_max)),
        "max_value": max_val,
        "lesion_pixel_count": lesion_pixels
    }


def compute_attribution_mass(
    heatmap: Union[torch.Tensor, np.ndarray],
    lesion_mask: Union[torch.Tensor, np.ndarray]
) -> Dict[str, Any]:
    """
    Calculates the Attribution Mass (Energy in Saliency): the proportion of total
    heatmap energy that falls inside the ground-truth lesion mask.

    Formula:
        Attribution Mass = sum(Heatmap * (Mask > 0)) / sum(Heatmap)

    Returns:
        Dict containing 'attribution_mass' in [0.0, 1.0] and execution status.
    """
    hm_np, mask_np = validate_heatmap_and_mask(heatmap, lesion_mask)

    total_energy = float(np.sum(hm_np))
    if total_energy <= 1e-12:
        return {
            "attribution_mass": 0.0,
            "status": "zero_energy_heatmap",
            "reason": "Total heatmap energy is zero.",
            "inside_energy": 0.0,
            "total_energy": 0.0
        }

    lesion_binary = (mask_np > 0).astype(np.float32)
    inside_energy = float(np.sum(hm_np * lesion_binary))

    if np.sum(lesion_binary) == 0:
        return {
            "attribution_mass": 0.0,
            "status": "empty_mask",
            "reason": "Lesion mask contains no positive pixels.",
            "inside_energy": 0.0,
            "total_energy": total_energy
        }

    mass = float(np.clip(inside_energy / total_energy, 0.0, 1.0))
    return {
        "attribution_mass": mass,
        "status": "evaluated",
        "inside_energy": inside_energy,
        "total_energy": total_energy
    }


def compute_explanation_iou(
    heatmap: Union[torch.Tensor, np.ndarray],
    lesion_mask: Union[torch.Tensor, np.ndarray],
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Calculates spatial Intersection over Union (IoU) and Dice coefficient between
    a thresholded binary Grad-CAM heatmap and the ground-truth lesion mask.

    Args:
        heatmap: 2D float array in [0.0, 1.0].
        lesion_mask: 2D array of lesion annotations.
        threshold: Binarization threshold for Grad-CAM activations (default: 0.5).

    Returns:
        Dict containing 'iou', 'dice', intersection pixel counts, and status.
    """
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"Binarization threshold must be in [0.0, 1.0], got {threshold}")

    hm_np, mask_np = validate_heatmap_and_mask(heatmap, lesion_mask)

    bin_cam = (hm_np >= threshold)
    bin_mask = (mask_np > 0)

    intersection = int(np.logical_and(bin_cam, bin_mask).sum())
    union = int(np.logical_or(bin_cam, bin_mask).sum())
    cam_pos = int(bin_cam.sum())
    mask_pos = int(bin_mask.sum())

    if union == 0:
        # Both heatmap and mask have zero positive pixels
        return {
            "iou": None,
            "dice": None,
            "status": "empty_union",
            "reason": "Both thresholded heatmap and lesion mask are empty.",
            "intersection_pixels": 0,
            "cam_positive_pixels": 0,
            "mask_positive_pixels": 0,
            "threshold": threshold
        }

    iou = float(intersection / union)
    dice = float((2.0 * intersection) / (cam_pos + mask_pos)) if (cam_pos + mask_pos) > 0 else 0.0

    return {
        "iou": iou,
        "dice": dice,
        "status": "evaluated",
        "intersection_pixels": intersection,
        "union_pixels": union,
        "cam_positive_pixels": cam_pos,
        "mask_positive_pixels": mask_pos,
        "threshold": threshold
    }


def evaluate_explanation_batch(
    heatmaps: List[Any],
    lesion_masks: List[Any],
    threshold: float = 0.5,
    original_sizes: Optional[List[Tuple[int, int]]] = None,
    crop_boxes: Optional[List[Optional[Tuple[int, int, int, int]]]] = None
) -> Dict[str, Any]:
    """
    Evaluates explanation localization over a batch of images and corresponding lesion masks.

    Handles:
        - Missing annotations (None masks are skipped and tracked).
        - Cropped heatmaps (projects back to original mask space if crop_boxes are supplied).
        - Aggregates Pointing Game Accuracy, Mean Attribution Mass, and Mean IoU over evaluable cases.

    Returns:
        Structured evaluation report.
    """
    if len(heatmaps) != len(lesion_masks):
        raise ValueError(
            f"Batch count mismatch: {len(heatmaps)} heatmaps vs {len(lesion_masks)} lesion masks."
        )

    n_total = len(heatmaps)
    pointing_hits = 0
    pointing_evaluable = 0

    attribution_masses = []
    ious = []
    dices = []

    skipped_none = 0
    skipped_empty_mask = 0
    evaluated_cases = 0

    case_details = []

    for idx, (hm, mask) in enumerate(zip(heatmaps, lesion_masks)):
        if mask is None:
            skipped_none += 1
            case_details.append({
                "case_index": idx,
                "status": "skipped_missing_mask",
                "reason": "No ground-truth lesion mask supplied."
            })
            continue

        hm_2d = to_2d_numpy(hm, name=f"heatmap_{idx}")
        mask_2d = to_2d_numpy(mask, name=f"mask_{idx}")

        # Align cropped heatmap to full mask if projection details are supplied
        if (
            original_sizes is not None
            and crop_boxes is not None
            and project_heatmap_to_original is not None
            and crop_boxes[idx] is not None
        ):
            hm_2d = project_heatmap_to_original(hm_2d, original_sizes[idx], crop_boxes[idx])

        # If spatial sizes still differ, raise error
        if hm_2d.shape != mask_2d.shape:
            raise ValueError(
                f"Case {idx}: Heatmap shape {hm_2d.shape} does not match mask shape {mask_2d.shape}."
            )

        pg_res = evaluate_pointing_game(hm_2d, mask_2d)
        am_res = compute_attribution_mass(hm_2d, mask_2d)
        iou_res = compute_explanation_iou(hm_2d, mask_2d, threshold=threshold)

        if pg_res["status"] == "empty_mask":
            skipped_empty_mask += 1
        elif pg_res["status"] == "evaluated":
            pointing_evaluable += 1
            if pg_res["hit"]:
                pointing_hits += 1

        if am_res["status"] == "evaluated":
            attribution_masses.append(am_res["attribution_mass"])

        if iou_res["status"] == "evaluated":
            ious.append(iou_res["iou"])
            dices.append(iou_res["dice"])

        evaluated_cases += 1
        case_details.append({
            "case_index": idx,
            "status": "evaluated",
            "pointing_game": pg_res,
            "attribution_mass": am_res,
            "iou_dice": iou_res
        })

    pg_accuracy = float(pointing_hits / pointing_evaluable) if pointing_evaluable > 0 else None
    mean_mass = float(np.mean(attribution_masses)) if len(attribution_masses) > 0 else None
    mean_iou = float(np.mean(ious)) if len(ious) > 0 else None
    mean_dice = float(np.mean(dices)) if len(dices) > 0 else None

    return {
        "status": "success",
        "counts": {
            "total_cases": n_total,
            "evaluated_cases": evaluated_cases,
            "skipped_missing_masks": skipped_none,
            "empty_mask_cases": skipped_empty_mask,
            "pointing_evaluable_cases": pointing_evaluable
        },
        "aggregate_metrics": {
            "pointing_game_accuracy": pg_accuracy,
            "mean_attribution_mass": mean_mass,
            "mean_iou": mean_iou,
            "mean_dice": mean_dice,
            "binarization_threshold": threshold
        },
        "case_details": case_details
    }
