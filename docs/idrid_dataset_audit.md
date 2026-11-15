# IDRiD Dataset Comprehensive Audit & Feasibility Report

**Project:** Explainable AI System for Diabetic Retinopathy Screening (`Eyeris`)  
**Role:** Member 2 (Image Quality Assessment, Retinal Image Preprocessing, and Lesion Segmentation)  
**Dataset Path:** `data/raw/IDRiD/`  
**Audit Date:** November 15, 2026  
**Status:** Completed & Validated  

---

## 1. Executive Summary

A comprehensive pre-implementation audit of the Indian Diabetic Retinopathy Image Dataset (IDRiD) was conducted across all three sub-datasets:
1. **A. Segmentation** (81 images with pixel-level ground truth masks for lesions and optic disc)
2. **B. Disease Grading** (516 images with clinical DR and DME severity ground truths)
3. **C. Localization** (516 images with pixel coordinate markups for Optic Disc center and Fovea center)

All original data files, folder hierarchies, and ground truth annotations are intact and verified. No raw dataset files have been modified, renamed, moved, or staged into Git.

---

## 2. Directory Hierarchy & Dataset Structure

The three IDRiD components extracted under `data/raw/IDRiD/` have the following structure:

```text
data/raw/IDRiD/
├── A. Segmentation/
│   ├── 1. Original Images/
│   │   ├── a. Training Set/                       # 54 images (IDRiD_01.jpg to IDRiD_54.jpg)
│   │   └── b. Testing Set/                        # 27 images (IDRiD_55.jpg to IDRiD_81.jpg)
│   ├── 2. All Segmentation Groundtruths/
│   │   ├── a. Training Set/
│   │   │   ├── 1. Microaneurysms/                 # 54 binary masks (*_MA.tif)
│   │   │   ├── 2. Haemorrhages/                   # 53 binary masks (*_HE.tif) [IDRiD_43 absent]
│   │   │   ├── 3. Hard Exudates/                  # 54 binary masks (*_EX.tif)
│   │   │   ├── 4. Soft Exudates/                  # 26 binary masks (*_SE.tif) [28 absent]
│   │   │   └── 5. Optic Disc/                     # 54 binary masks (*_OD.tif)
│   │   └── b. Testing Set/
│   │       ├── 1. Microaneurysms/                 # 27 binary masks (*_MA.tif)
│   │       ├── 2. Haemorrhages/                   # 27 binary masks (*_HE.tif)
│   │       ├── 3. Hard Exudates/                  # 27 binary masks (*_EX.tif)
│   │       ├── 4. Soft Exudates/                  # 14 binary masks (*_SE.tif) [13 absent]
│   │       └── 5. Optic Disc/                     # 27 binary masks (*_OD.tif)
│   ├── CC-BY-4.0.txt
│   └── LICENSE.txt
├── B. Disease Grading/
│   ├── 1. Original Images/
│   │   ├── a. Training Set/                       # 413 images (IDRiD_001.jpg to IDRiD_413.jpg)
│   │   └── b. Testing Set/                        # 103 images (IDRiD_001.jpg to IDRiD_103.jpg)
│   ├── 2. Groundtruths/
│   │   ├── a. IDRiD_Disease Grading_Training Labels.csv  # 413 labels (DR grade 0-4, DME risk 0-2)
│   │   └── b. IDRiD_Disease Grading_Testing Labels.csv   # 103 labels (DR grade 0-4, DME risk 0-2)
│   ├── CC-BY-4.0.txt
│   └── LICENSE.txt
└── C. Localization/
    ├── 1. Original Images/
    │   ├── a. Training Set/                       # 413 images (Identical image set to B. Training)
    │   └── b. Testing Set/                        # 103 images (Identical image set to B. Testing)
    ├── 2. Groundtruths/
    │   ├── 1. Optic Disc Center Location/
    │   │   ├── a. IDRiD_OD_Center_Training Set_Markups.csv  # 413 (X, Y) coordinates
    │   │   └── b. IDRiD_OD_Center_Testing Set_Markups.csv   # 103 (X, Y) coordinates
    │   └── 2. Fovea Center Location/
    │       ├── IDRiD_Fovea_Center_Training Set_Markups.csv  # 413 (X, Y) coordinates
    │       └── IDRiD_Fovea_Center_Testing Set_Markups.csv   # 103 (X, Y) coordinates
    ├── CC-BY-4.0.txt
    └── LICENSE.txt
```

---

## 3. Image Properties & Technical Specifications

| Parameter | Original Images (`.jpg`) | Groundtruth Masks (`.tif`) | Markups & Labels (`.csv`) |
| :--- | :--- | :--- | :--- |
| **Spatial Resolution** | `4288 x 2848` (Width x Height) | `4288 x 2848` (Identical 1:1) | Pixel coordinates $(X, Y)$ normalized to original dimensions |
| **Color Space / Channels** | RGB (3-channel, 24-bit) | Single-channel binary (`uint8`), values $\{0, 1\}$ | Tabular text |
| **Compression / Format** | JPEG (lossy, high quality) | TIFF (uncompressed binary mask) | Comma-Separated Values (UTF-8) |
| **Aspect Ratio** | ~3:2 ($1.5056 : 1$) | ~3:2 ($1.5056 : 1$) | N/A |
| **Corrupted / Unreadable Files** | **0** (All 1,113 image files validated) | **0** (All 363 mask files validated) | **0** (All 6 CSV files validated) |

---

## 4. Lesion Classes & Mask Census

### A. Annotated Classes
IDRiD provides ground truth masks for 4 distinct pathological lesions and 1 anatomical landmark:
1. **Microaneurysms (MA):** Focal dilatations of retinal capillaries, appearing as tiny circular red dots. Earliest sign of DR.
2. **Haemorrhages (HE):** Ruptures of retinal vessels (dot, blot, or flame-shaped red lesions). Indicator of non-proliferative/proliferative DR.
3. **Hard Exudates (EX):** Extravasated lipid and protein deposits, appearing as sharp-margined, waxy, yellowish patches.
4. **Soft Exudates / Cotton Wool Spots (SE):** Micro-infarcts of the nerve fiber layer, appearing as fluffy, pale white lesions with indistinct margins.
5. **Optic Disc (OD):** Normal anatomical landmark (optic nerve head entry point), vital for landmark localization and distinguishing exudates from disc tissue.

### B. Image and Mask Count Census

| Target Class | Training Set Images | Training Set Masks | Testing Set Images | Testing Set Masks | Total Masks Present | Absence / Zero-Lesion Count |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Microaneurysms (MA)** | 54 | 54 | 27 | 27 | **81** | 0 images (Present in 100% of cases) |
| **Haemorrhages (HE)** | 54 | 53 | 27 | 27 | **80** | 1 image in Train (`IDRiD_43`) has zero HE |
| **Hard Exudates (EX)** | 54 | 54 | 27 | 27 | **81** | 0 images (Present in 100% of cases) |
| **Soft Exudates (SE)** | 54 | 26 | 27 | 14 | **40** | 28 images in Train, 13 in Test have zero SE |
| **Optic Disc (OD)** | 54 | 54 | 27 | 27 | **81** | 0 images (Present in 100% of cases) |
| **Total Files** | **54** | **241** | **27** | **122** | **363** | — |

---

## 5. File Correspondence & Missing Mask Handling

1. **Naming Conventions:**
   * Images: `IDRiD_{01..54}.jpg` (Train), `IDRiD_{55..81}.jpg` (Test).
   * Masks: `IDRiD_{id}_{MA|HE|EX|SE|OD}.tif`.
   * Filenames correspond systematically to their parent images.
2. **Missing Mask Semantics:**
   * In IDRiD, missing mask files represent **clinical absence** of the lesion in that eye, **not corrupted or lost files**.
   * Specifically:
     * `IDRiD_43` has no Haemorrhages (`_HE.tif`).
     * 28 Training images (`IDRiD_01`, `02`, `04`, `05`, `06`, `07`, `09`, `10`, `11`, `12`, `15`, `16`, `20`, `21`, `24`, `26`, `27`, `28`, `29`, `34`, `36`, `37`, `40`, `41`, `42`, `43`, `44`, `45`) have no Soft Exudates (`_SE.tif`).
     * 13 Testing images (`IDRiD_57`, `58`, `62`, `63`, `65`, `66`, `69`, `76`, `77`, `78`, `79`, `80`, `81`) have no Soft Exudates (`_SE.tif`).
3. **Dataset Pipeline Rule:**
   * When loading ground truth masks for training or evaluation, any absent file must be automatically populated with an all-zero binary array of shape `(2848, 4288)`.

---

## 6. Lesion Pixel Sparsity & Imbalance Analysis

Empirical calculation of lesion area coverage across all training ground truth masks ($2848 \times 4288 = 12,211,904$ pixels per image):

| Class | Mean Area (% of Image) | Min Area (%) | Max Area (%) | Pixel Sparsity Nature |
| :--- | :---: | :---: | :---: | :--- |
| **Microaneurysms (MA)** | **0.1069%** | 0.0066% | 0.3117% | Extreme sparsity (~1 in 1,000 pixels); tiny punctate structures |
| **Soft Exudates (SE)** | **0.3934%** | 0.0272% | 1.2944% | Highly sparse; completely absent in 50% of patients |
| **Hard Exudates (EX)** | **0.8067%** | 0.0192% | 6.5938% | Moderate sparsity; clustered around macula/fovea |
| **Haemorrhages (HE)** | **1.0043%** | 0.0176% | 14.9139% | Wide variation; localized petechiae up to massive subretinal bleeds |
| **Optic Disc (OD)** | **1.8055%** | 1.0045% | 2.7625% | Consistent anatomical area (~1.5% to 2.5% of fundus) |

**Key Implication:** Because foreground lesion pixels account for less than 1% of total pixels, standard Cross-Entropy Loss will succumb to background dominance (achieving >99% trivial accuracy with 0 Dice). A composite **Dice Loss + Binary Cross-Entropy Loss** or **Focal Tversky Loss** is mandatory.

---

## 7. Dataset Utilization Strategy Across Modules

| Dataset Module | Sample Count | Primary Designated Responsibility | Secondary / Testing Value |
| :--- | :---: | :--- | :--- |
| **A. Segmentation** | 81 images (54 train / 27 test) | **Lesion Segmentation Model:** End-to-end training, validation, and benchmarking of U-Net segmentation. | Preprocessing & Quality verification on paired ground truth cases. |
| **B. Disease Grading** | 516 images (413 train / 103 test) | **Image Quality Assessment & Preprocessing:** Validation of contrast enhancement (Ben Graham), FOV circular cropping, blur detection, and illumination grading across all 5 DR grades (0 to 4). | Cross-functional support for Member 1 (Classifier) and Member 4 (Screening pipeline). |
| **C. Localization** | 516 images (413 train / 103 test) | **Landmark Validation:** Ground truth $(X, Y)$ coordinates for Optic Disc and Fovea centers validate whether quality assessment correctly flags macula/disc occlusion. | Verification of FOV centering and anatomical orientation. |

---

## 8. Architectural Determination: Binary vs. Multi-Class Segmentation

### A. Empirical Finding: Spatial Co-occurrence & Overlap
* Analysis of the 54 training images revealed that **21 out of 54 images (38.9%) have overlapping lesion pixels** between distinct ground truth masks (e.g., hard exudates adjacent to or overlapping haemorrhages; microaneurysms embedded within larger haemorrhagic fields).

### B. Evaluation of Segmentation Paradigms
1. **Mutually Exclusive Multi-Class (Softmax Output):**
   * *Mechanism:* Pixel $p \in \{0, 1, 2, 3, 4, 5\}$ where $\sum_{c=0}^5 P(c|p) = 1$.
   * *Problem:* Forces each pixel to choose exactly one class. Overlapping pathological features are forcibly suppressed, introducing label noise, under-segmentation, and gradient interference between tiny MAs and large HEs.
   * *Verdict:* **Mathematically & Clinically Inappropriate.**
2. **Multi-Label / Multi-Channel Architecture (Sigmoid Output):**
   * *Mechanism:* Single U-Net encoder-decoder backbone with an output layer of shape `(B, 4, H, W)`. Each channel predicts a single lesion type independently via a `Sigmoid` activation: $P(C_i|p) \in [0, 1]$.
   * *Advantages:* Allows spatial co-occurrence; shared feature representation; computationally efficient.
3. **Independent Binary U-Net Models:**
   * *Mechanism:* 4 separate binary segmentation models (`U-Net_MA`, `U-Net_HE`, `U-Net_EX`, `U-Net_SE`).
   * *Advantages:* Maximum flexibility in per-lesion hyperparameter tuning, patch size selection, and loss weighting. Prevents large lesions (HE) from overwhelming small lesions (MA).
   * *Drawbacks:* $4\times$ memory and inference cost.

### C. Recommendation
* Implement a **Multi-Channel Multi-Label U-Net with Sigmoid activations** as the primary architecture, paired with independent binary Dice evaluation metrics.
* Maintain modular interfaces in `ai_models/segmentation/` so that specialized binary heads or separate binary models can be plugged in seamlessly without breaking the pipeline.

---

## 9. Recommended Training and Validation Strategy

### A. Cross-Validation on Small Sample Size ($N = 54$)
* A single static train/validation split (e.g., 44 train / 10 val) creates extreme performance variance due to individual patient lesion variations.
* **Recommendation:** **5-Fold Cross-Validation** on the 54 training images.
* Reserve the official 27 testing images strictly as the **untouched test benchmark**.

### B. Resolution & VRAM Management (RTX 3050 6GB)
* Raw resolution ($4288 \times 2848$) will trigger CUDA Out-Of-Memory (OOM) errors during backpropagation.
* **Two-Tier Preprocessing Pipeline:**
  1. **Tier 1 (Global Context U-Net):** Crop circular FOV to eliminate 40% empty black background; resize to $512 \times 512$ or $768 \times 768$ with Ben Graham color normalization.
  2. **Tier 2 (High-Resolution Patching for Microaneurysms):** Extract $512 \times 512$ overlapping patches at native resolution centered on candidate lesion regions to preserve fine microvascular details.

### C. Data Augmentation Protocol
* Fundus images possess rotational symmetry:
  * Random 90°, 180°, 270° rotations + random continuous rotation ($\pm 15^\circ$).
  * Random horizontal and vertical flips.
  * Mild brightness and contrast jittering ($\pm 10\%$).
  * Elastic deformations / Affine scaling ($0.95 - 1.05$).

### D. Objective Function
$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{BCE}} + \lambda \mathcal{L}_{\text{Dice}}$$
where $\mathcal{L}_{\text{Dice}} = 1 - \frac{2 |Y \cap \hat{Y}| + \epsilon}{|Y| + |\hat{Y}| + \epsilon}$ with Laplace smoothing ($\epsilon = 1.0$).

---

## 10. Audit Compliance & Next Steps

* **Strict Rule Compliance:**
  * No original files deleted or renamed.
  * No synthetic/fabricated annotations introduced.
  * No model training initiated.
  * `data/raw/*` is confirmed gitignored.
* **Ready for Implementation:**
  * Phase 1: Retinal Image Quality Assessment (`computer_vision/image_quality/`)
  * Phase 2: Retinal Preprocessing Pipeline (`computer_vision/preprocessing/`)
  * Phase 3: PyTorch U-Net & Multi-Label Segmentation (`ai_models/segmentation/`)

---

## 11. IDRiD Dataset Loader Usage Guide

The PyTorch dataset and dataloader implementation is located at:
`ai_models/segmentation/dataset.py`

### A. Quick Start: Loading Batches with DataLoaders

```python
from ai_models.segmentation.dataset import create_segmentation_dataloaders

# Create reproducible DataLoaders for train, val, and test splits
loaders = create_segmentation_dataloaders(
    root_dir="data/raw/IDRiD",
    batch_size=4,
    val_fraction=0.2,       # 43 train images, 11 validation images
    seed=42,                # Fixed seed: guarantees zero data leakage
    img_size=(512, 512),    # (H, W) spatial resolution
    num_workers=0,          # Recommended 0 on Windows
)

train_loader = loaders["train"]
val_loader = loaders["val"]
test_loader = loaders["test"]

# Iterate over a training batch
for batch in train_loader:
    images = batch["image"]           # Shape: (B, 3, 512, 512) - float normalized
    masks = batch["masks"]           # Shape: (B, 4, 512, 512) - float {0.0, 1.0}
    mask_valid = batch["mask_valid"] # Shape: (B, 4) - bool (True if annotated)
    image_ids = batch["image_id"]     # List of str, e.g. ['IDRiD_01', 'IDRiD_02']
    break
```

### B. Channel Mapping for Lesion Masks

The 4 channels in `batch["masks"]` and `batch["mask_valid"]` correspond strictly to:
- Channel `0`: **MA** (Microaneurysms)
- Channel `1`: **HE** (Haemorrhages)
- Channel `2`: **EX** (Hard Exudates)
- Channel `3`: **SE** (Soft Exudates)

### C. Proper Missing Mask Loss Masking

When training, unannotated lesion classes (e.g. `IDRiD_43` for HE or unannotated SE cases) are explicitly identified by `mask_valid == False`. Compute loss strictly over valid annotations:

```python
import torch.nn.functional as F

# Example: Masked Binary Cross Entropy
bce_raw = F.binary_cross_entropy_with_logits(predictions, masks, reduction="none")
# bce_raw shape: (B, 4, H, W)

# Weight by valid mask presence
weight = mask_valid.unsqueeze(-1).unsqueeze(-1).float()  # (B, 4, 1, 1)
masked_loss = (bce_raw * weight).sum() / weight.sum().clamp(min=1.0)
```

### D. Running Unit Tests

Run the full dataset test suite with pytest:

```powershell
pytest tests/unit/test_idrid_dataset.py -v
```

---
*Report and documentation compiled and verified by Member 2.*


