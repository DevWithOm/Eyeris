# Member 2 Handover Documentation: Image Quality & Lesion Segmentation

**Author:** Member 2 (Computer Vision & Segmentation Specialist)  
**Recipient:** Member 4 (System Integration & Full-Stack Pipeline Lead)  
**Branch:** `feature/quality-segmentation`  
**Target Integration Branch:** `integration/member-4`  
**Date:** November 15, 2026  

---

## 1. Overview & Assigned Responsibilities

Member 2 is responsible for the front-end optical and anatomical pipeline of the **Eyeris Explainable AI Retinal Screening System**:
1. **Retinal Image Quality Assessment (IQA):** Determining fundus gradability, focus sharpness, exposure, glare, and field-of-view integrity.
2. **Retinal Image Preprocessing:** Standardized resizing, normalization, and mask-preserving spatial transformations.
3. **Multi-Class Lesion Segmentation:** Deep-learning segmentation of the 4 cardinal diabetic retinopathy lesions:
   - **Microaneurysms (MA)**
   - **Haemorrhages (HE)**
   - **Hard Exudates (EX)**
   - **Soft Exudates / Cotton-Wool Spots (SE)**
4. **Explainability Overlays:** Color-coded lesion visual overlays for clinician review.

All components adhere strictly to the shared repository contracts under both `computer_vision/` and `ai_models/`, as well as `src/vision/`.

---

## 2. Directory Structure & Files Delivered

```
Eyeris/
├── ai_models/
│   └── segmentation/
│       ├── __init__.py           # Unified exports for Member 4
│       ├── dataset.py            # IDRiDDataset & IDRiDPatchDataset loader
│       ├── evaluate.py           # Evaluation functions & metric calculators
│       ├── predict.py            # segment_lesions & generate_lesion_overlay
│       ├── train.py              # Segmentation training engine
│       └── unet.py               # U-Net PyTorch architecture
├── computer_vision/
│   └── image_quality/
│       └── __init__.py           # assess_quality re-export
├── src/
│   └── vision/
│       ├── quality.py            # Core image quality assessment engine
│       └── segmentation/
│           ├── config.py         # SegmentationConfig dataclass
│           ├── config.yaml       # Hyperparameters configuration
│           ├── losses.py         # MaskedBCELoss, SoftDiceLoss, CombinedSegmentationLoss
│           ├── metrics.py        # Dice, IoU, Precision, Recall calculators
│           ├── model.py          # PyTorch UNet (DoubleConv, Skip Connections, Sigmoid)
│           ├── predict.py        # Inference & visual overlay generator
│           └── train.py          # Training, early stopping, and plotting engine
├── scripts/
│   ├── prepare_patches.py        # Full-resolution lesion patch generator
│   └── train_segmentation.py     # End-to-end training and benchmark script
├── outputs/segmentation/         # (Git-ignored artifacts)
│   ├── checkpoints/              # best_model.pth (Epoch 25 GPU, 0.4199 Dice)
│   ├── logs/                     # training_history.json & config.yaml
│   ├── plots/                    # loss_curves.png, metrics_curves.png, per_class_dice.png
│   └── predictions/              # Validation comparison figures
├── docs/
│   ├── idrid_dataset_audit.md    # Initial dataset audit and lesion statistics
│   ├── segmentation_training_report.md # Comprehensive 25-epoch evaluation report
│   └── member2_handover.md       # This handover specification
└── tests/unit/
    ├── test_quality.py           # 11 tests for quality assessment
    ├── test_idrid_dataset.py     # 9 tests for dataset loading and splitting
    └── test_segmentation.py      # 8 tests for model, loss, metrics, and inference
```

---

## 3. Integration Interface & Usage for Member 4

Member 4 can import and use Member 2's components directly using standard Python interfaces without modifying inner modules.

### A. Retinal Image Quality Assessment

```python
from computer_vision.image_quality import assess_quality

# Acceptable inputs: file path (str/Path), PIL.Image, or numpy.ndarray (RGB/BGR)
result = assess_quality("path/to/retinal_fundus.jpg")

# Expected Output Format:
{
    "status": "GRADABLE",             # "GRADABLE" | "UNGRADABLE" | "REVIEW_REQUIRED"
    "quality_score": 0.88,            # Float in [0.0, 1.0]
    "blur_score": 142.5,              # Variance of Laplacian on eroded green channel
    "illumination_score": 0.79,       # Brightness and contrast score
    "field_of_view_status": "OPTIMAL",# "OPTIMAL" | "ACCEPTABLE" | "RESTRICTED" | "UNKNOWN"
    "reason_codes": [],               # e.g., ["BLURRED", "UNDEREXPOSED", "OVEREXPOSED_GLARE"]
    "recapture_suggestion": None      # Human-readable instruction if ungradable
}
```

### B. Single-Image Lesion Segmentation & Overlay Generation

```python
from ai_models.segmentation import segment_lesions

result = segment_lesions(
    image_input="path/to/retinal_fundus.jpg",
    output_dir="storage/predictions",   # Destination for saved masks and overlays
    checkpoint_path="outputs/segmentation/checkpoints/best_model.pth", # Optional
    device="cuda"                       # Automatically falls back to CPU if unavailable
)

# Expected Output Format:
{
    "status": "SUCCESS",                # "SUCCESS" | "FAILED" | "SKIPPED_UNGRADABLE"
    "lesion_detected": True,            # True if any lesion exceeds threshold
    "lesion_counts": {                  # Count of connected components per lesion
        "MA": 4,
        "HE": 2,
        "EX": 8,
        "SE": 1
    },
    "lesion_area_ratio": {              # Fraction of image canvas occupied by lesion
        "MA": 0.0012,
        "HE": 0.0045,
        "EX": 0.0120,
        "SE": 0.0031
    },
    "confidence": {                     # Mean prediction confidence in positive regions
        "MA": 0.72,
        "HE": 0.81,
        "EX": 0.91,
        "SE": 0.85
    },
    "mask_path": "storage/predictions/pred_masks_composite.png",
    "overlay_path": "storage/predictions/pred_overlay_color.jpg",
    "metadata": {
        "classes": ["MA", "HE", "EX", "SE"],
        "checkpoint_used": "outputs/segmentation/checkpoints/best_model.pth",
        "device": "cuda"
    }
}
```

### C. Color-Coded Overlay Contract

Overlays are generated by blending semi-transparent lesion masks over the original fundus image ($\alpha = 0.45$):
- **Microaneurysms (MA):** Bright Red `BGR: (0, 0, 255)`
- **Haemorrhages (HE):** Dark Crimson `BGR: (0, 0, 139)`
- **Hard Exudates (EX):** Yellow `BGR: (0, 255, 255)`
- **Soft Exudates (SE):** Cyan `BGR: (255, 255, 0)`

---

## 4. Trained Weights & Checkpoints

Checkpoints are stored locally under `outputs/segmentation/checkpoints/` and are excluded from Git by `.gitignore`:

| Checkpoint Name | File Size | Description / Performance | Recommended Use |
| :--- | :---: | :--- | :--- |
| **`best_model.pth`** | **52.3 MB** | **Epoch 25 GPU Model** (Mean Dice: **0.4199**, EX: **0.6638**, SE: **0.6602**, HE: **0.3620**, MA: **0.1908**) | **Production / Primary Inference** |
| `best_model_prev.pth` | 52.3 MB | Epoch 24 GPU Model (Mean Dice: 0.4056) | Preserved historical backup |
| `best_model_cpu_dice_0.2476.pth` | 13.1 MB | Epoch 5 CPU Model (16 channels, Mean Dice: 0.2476) | Lightweight CPU fallback |
| `latest_checkpoint.pth` | 52.3 MB | Full training state (optimizer + scheduler) | Resume training if required |

*Note for Member 4: If deploying on a server without GPU, `best_model.pth` loads seamlessly on CPU via `torch.load(..., map_location="cpu")` (handled automatically by `segment_lesions`).*

---

## 5. Dataset Preparation & Training Reproducibility

To re-run or inspect the pipeline:

1. **Dataset Location:** Raw IDRiD images and masks reside under `data/raw/IDRiD/A. Segmentation/` (git-ignored).
2. **Patch Extraction:**
   ```powershell
   python scripts/prepare_patches.py
   ```
   Generates 533 training and 135 validation full-resolution crops under `data/processed/IDRiD_patches/`.
3. **Training Execution:**
   ```powershell
   python scripts/train_segmentation.py
   ```
   Automatically detects CUDA GPU or CPU, trains the U-Net, calculates Dice/IoU per lesion class, saves checkpoints with previous version preservation, and outputs metric curves to `outputs/segmentation/plots/`.

---

## 6. Verification & Test Suite Summary

The unit and integration test suite was executed on branch `feature/quality-segmentation`:

```powershell
pytest tests/unit/ -v
```

**Results: 29 passed, 0 failed, 0 warnings (100% pass rate in 16.8s)**
- `test_idrid_dataset.py`: 9/9 PASSED (Pairing, dimensions, binary values, missing annotation handling, zero-leakage split, DataLoader batches).
- `test_quality.py`: 11/11 PASSED (Sharpness, illumination, underexposure, glare, FOV, blank images, unreadable files, PIL/NumPy inputs).
- `test_segmentation.py`: 8/8 PASSED (U-Net dimensions, probability outputs, masked loss gradient zeroing, metrics, early stopping, overlay generation, single-image inference, YAML config serialization).
- `test_project_smoke.py`: 1/1 PASSED.

---

## 7. Known Limitations & Clinical Disclaimer

1. **Microaneurysm (MA) Sensitivity:**
   MAs are small ($< 15\,\mu\text{m}$) circular vascular structures. While patch-based training improved MA Dice to 0.1908, faint MAs near vessel bifurcations may occasionally be missed.
2. **Dataset Size:**
   Trained on 54 expert-annotated images from the IDRiD cohort. While patch sampling expanded this to 668 patches, external generalization across non-IDRiD camera models (e.g. Topcon vs Canon) should be verified.
3. **Clinical Disclaimer:**
   This module is developed as a technical and educational prototype for the Smart India Hackathon (SIH). It is **not clinically certified** and must **not** be used as a standalone diagnostic instrument without certified ophthalmologist validation.

---

## 8. Pull Request & Branch Information

- **Working Branch:** `feature/quality-segmentation`
- **Target Integration Branch:** `integration/member-4`
- **Git Status:** Clean working tree. Datasets (`data/raw/`, `*.zip`) and checkpoints (`outputs/`) are strictly git-ignored.
- **Commit Notice:** No commits have been made directly to `main`.

