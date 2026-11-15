"""Extracts full-optical-resolution 256x256 patches centered on lesions from IDRiD images.

Key Guarantees:
1. Patient-level split: patches from train images go strictly to train/, val images to val/.
2. High lesion density: patches capture microaneurysms and exudates at full native resolution.
3. Preserves co-occurrence: all 4 lesion classes are cropped simultaneously for each patch.
4. Preserves missing annotation tracking: `mask_valid` flags are tracked per patch.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_models.segmentation.dataset import (
    LESION_CLASSES,
    LESION_FOLDER_MAP,
    LESION_SUFFIX_MAP,
    split_idrid_dataset,
)


def extract_patches_for_image(
    image_path: Path,
    masks_dict: Dict[str, Optional[np.ndarray]],
    mask_valid: Dict[str, bool],
    patch_size: int = 256,
    samples_per_lesion: int = 3,
    bg_samples: int = 2,
    seed: int = 42,
) -> List[Dict]:
    """Extracts candidate center coordinates for lesion-centered and background patches."""
    with Image.open(image_path) as im:
        img_w, img_h = im.size

    rng = np.random.RandomState(seed + int(image_path.stem.split("_")[-1]))
    centers: List[Tuple[int, int, str]] = []

    # 1. Lesion-centered points
    for c in LESION_CLASSES:
        if mask_valid[c] and masks_dict[c] is not None:
            mask_arr = masks_dict[c]
            ys, xs = np.where(mask_arr > 0)
            if len(ys) > 0:
                # Select evenly distributed positive coordinates
                indices = np.linspace(0, len(ys) - 1, min(samples_per_lesion, len(ys)), dtype=int)
                for idx in indices:
                    centers.append((int(ys[idx]), int(xs[idx]), c))

    # 2. Background fundus points (inside retina, no lesions)
    # Sum all available lesion masks
    union_lesions = np.zeros((img_h, img_w), dtype=bool)
    for c in LESION_CLASSES:
        if masks_dict[c] is not None:
            union_lesions |= (masks_dict[c] > 0)

    # Fundus interior is roughly inside [0.2*H:0.8*H, 0.2*W:0.8*W]
    bg_candidates_y = rng.randint(int(0.2 * img_h), int(0.8 * img_h), size=bg_samples * 10)
    bg_candidates_x = rng.randint(int(0.2 * img_w), int(0.8 * img_w), size=bg_samples * 10)

    bg_count = 0
    for by, bx in zip(bg_candidates_y, bg_candidates_x):
        ymin = max(0, min(img_h - patch_size, by - patch_size // 2))
        xmin = max(0, min(img_w - patch_size, bx - patch_size // 2))
        patch_lesions = union_lesions[ymin : ymin + patch_size, xmin : xmin + patch_size]
        if np.sum(patch_lesions) == 0:
            centers.append((by, bx, "BG"))
            bg_count += 1
            if bg_count >= bg_samples:
                break

    # 3. Crop patches
    patches_meta = []
    with Image.open(image_path) as im:
        img_rgb = im.convert("RGB")

    for i, (cy, cx, origin_class) in enumerate(centers):
        ymin = max(0, min(img_h - patch_size, cy - patch_size // 2))
        xmin = max(0, min(img_w - patch_size, cx - patch_size // 2))
        ymax = ymin + patch_size
        xmax = xmin + patch_size

        crop_img = img_rgb.crop((xmin, ymin, xmax, ymax))

        crop_masks = {}
        pos_counts = {}
        for c in LESION_CLASSES:
            if mask_valid[c] and masks_dict[c] is not None:
                c_m = masks_dict[c][ymin:ymax, xmin:xmax]
                crop_masks[c] = (c_m > 0).astype(np.uint8) * 255
                pos_counts[c] = int(np.sum(crop_masks[c] > 0))
            else:
                crop_masks[c] = None
                pos_counts[c] = 0

        patches_meta.append({
            "patch_index": i,
            "origin_class": origin_class,
            "bbox": (xmin, ymin, xmax, ymax),
            "pos_counts": pos_counts,
            "crop_img": crop_img,
            "crop_masks": crop_masks,
        })

    return patches_meta


def prepare_patch_dataset(
    root_dir: str = "data/raw/IDRiD",
    output_dir: str = "data/processed/IDRiD_patches",
    val_fraction: float = 0.2,
    seed: int = 42,
    patch_size: int = 256,
) -> Dict:
    """Prepares and saves train/val patch datasets."""
    start_time = time.time()
    out_path = (PROJECT_ROOT / output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    raw_root = (PROJECT_ROOT / root_dir).resolve()
    train_ids, val_ids, test_ids = split_idrid_dataset(
        root_dir=raw_root, val_fraction=val_fraction, seed=seed
    )

    splits = {"train": train_ids, "val": val_ids}
    summary = {"patch_size": patch_size, "splits": {}}

    img_dir = raw_root / "A. Segmentation" / "1. Original Images" / "a. Training Set"
    masks_base = raw_root / "A. Segmentation" / "2. All Segmentation Groundtruths" / "a. Training Set"

    for split_name, img_ids in splits.items():
        print(f"\n[*] Generating patches for split: '{split_name}' ({len(img_ids)} images)...")
        split_img_dir = out_path / split_name / "images"
        split_mask_dir = out_path / split_name / "masks"
        split_img_dir.mkdir(parents=True, exist_ok=True)
        split_mask_dir.mkdir(parents=True, exist_ok=True)

        split_patches = []
        total_pos_pixels = {c: 0 for c in LESION_CLASSES}

        for img_idx, img_id in enumerate(img_ids):
            img_path = img_dir / f"{img_id}.jpg"

            # Load masks and validity
            loaded_masks: Dict[str, Optional[np.ndarray]] = {}
            mask_valid: Dict[str, bool] = {}

            for c in LESION_CLASSES:
                f_name = LESION_FOLDER_MAP[c]
                s_name = LESION_SUFFIX_MAP[c]
                m_path = masks_base / f_name / f"{img_id}{s_name}"
                if m_path.exists():
                    with Image.open(m_path) as m_im:
                        loaded_masks[c] = np.array(m_im)
                    mask_valid[c] = True
                else:
                    loaded_masks[c] = None
                    mask_valid[c] = False

            patches = extract_patches_for_image(
                image_path=img_path,
                masks_dict=loaded_masks,
                mask_valid=mask_valid,
                patch_size=patch_size,
                samples_per_lesion=3,
                bg_samples=2,
                seed=seed,
            )

            for p in patches:
                pid = f"{img_id}_p{p['patch_index']:02d}_{p['origin_class']}"
                img_save_path = split_img_dir / f"{pid}.png"
                p["crop_img"].save(img_save_path)

                mask_paths_dict = {}
                for c in LESION_CLASSES:
                    if p["crop_masks"][c] is not None:
                        m_save_path = split_mask_dir / f"{pid}_{c}.png"
                        Image.fromarray(p["crop_masks"][c]).save(m_save_path)
                        mask_paths_dict[c] = str(m_save_path.relative_to(PROJECT_ROOT))
                        total_pos_pixels[c] += p["pos_counts"][c]
                    else:
                        mask_paths_dict[c] = None

                split_patches.append({
                    "patch_id": pid,
                    "parent_id": img_id,
                    "image_path": str(img_save_path.relative_to(PROJECT_ROOT)),
                    "mask_paths": mask_paths_dict,
                    "mask_valid": mask_valid,
                    "pos_counts": p["pos_counts"],
                    "origin_class": p["origin_class"],
                    "bbox": p["bbox"],
                })

            if (img_idx + 1) % 10 == 0 or (img_idx + 1) == len(img_ids):
                print(f"    - Processed {img_idx + 1}/{len(img_ids)} images -> {len(split_patches)} patches created.")

        summary["splits"][split_name] = {
            "num_images": len(img_ids),
            "num_patches": len(split_patches),
            "positive_pixels": total_pos_pixels,
            "patches": split_patches,
        }

    # Save summary metadata
    meta_file = out_path / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        # Save without full in-memory PIL images with safe integer casting
        json.dump(summary, f, indent=2, default=int)

    duration = round(time.time() - start_time, 2)
    print(f"\n[*] Patch preparation complete in {duration}s!")
    print(f"[*] Train Patches: {summary['splits']['train']['num_patches']}")
    print(f"[*] Val Patches:   {summary['splits']['val']['num_patches']}")
    print(f"[*] Metadata:      {meta_file}")
    return summary


if __name__ == "__main__":
    prepare_patch_dataset()
