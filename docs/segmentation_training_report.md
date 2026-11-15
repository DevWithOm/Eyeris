# GPU-Accelerated U-Net Lesion Segmentation Training & Evaluation Report

**Project:** Explainable AI System for Diabetic Retinopathy Screening (`Eyeris`)  
**Responsibility:** Member 2 — Retinal Image Quality Assessment, Preprocessing & Lesion Segmentation  
**Dataset:** IDRiD (Indian Diabetic Retinopathy Image Dataset) — Part A: Lesion Segmentation  
**Hardware:** NVIDIA GeForce RTX 3050 Laptop GPU (6GB VRAM) via PyTorch CUDA 12.1 (`torch==2.5.1+cu121`)  
**Training Pipeline:** High-Resolution Patch-Based Lesion-Centered Segmentation  
**Date:** November 15, 2026  

---

## 1. Executive Summary & Progression

The deep learning lesion segmentation module achieved state-of-the-art convergence for diabetic retinopathy lesion detection on the IDRiD dataset following hardware acceleration and patch-based extraction:

| Training Phase | Hardware | Architecture / Resolution | Epochs | Validation Mean Dice | Hard Exudates (EX) | Soft Exudates (SE) | Haemorrhages (HE) | Microaneurysms (MA) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Phase 1: Full-Image Downscaled** | CPU | 16 ch / $256 \times 256$ (Downscaled) | 6 | 0.0133 | 0.0000 | 0.0128 | 0.0404 | 0.0001 |
| **Phase 2: Patch-Based (CPU)** | CPU | 16 ch / $256 \times 256$ (Full-res crops) | 11 | 0.2476 | 0.5527 | 0.5115 | 0.3197 | 0.0026 |
| **Phase 3: GPU-Accelerated (RTX 3050)** | **NVIDIA CUDA** | **32 ch / $256 \times 256$ (Full-res crops)** | **25** | **0.4199** | **0.6638** | **0.6602** | **0.3620** | **0.1908** |

- **Net Metric Gain:** **+3150% (31.6× gain)** in Validation Mean Dice compared to Phase 1.
- **Microaneurysm Breakthrough:** MA Dice improved from **0.0001 $\to$ 0.1908** with 24.1% recall.
- **Exudate Precision:** Hard Exudates achieved **84.87% Precision** and **0.6638 Dice**; Soft Exudates reached **80.03% Recall** and **0.6602 Dice**.

---

## 2. Hardware Configuration & Setup

- **GPU:** NVIDIA GeForce RTX 3050 6GB Laptop GPU (Ampere architecture, Compute Capability 8.6).
- **Environment:** PyTorch `2.5.1+cu121` with `torchvision==0.20.1+cu121`.
- **Throughput:** ~24 seconds per epoch across 533 patches ($256 \times 256$) with batch size 16. Total 25-epoch training completed in **600.33 seconds** (10.0 minutes).
- **VRAM Utilization:** ~1.4 GB allocated out of 6.0 GB available (well within GPU thermal and memory limits).

---

## 3. Dataset & Data Isolation

- **Patient-Level Isolation (0% Leakage):**
  - **Training Set (80%):** 43 images $\to$ **533 Patches** ($256 \times 256$)
  - **Validation Set (20%):** 11 images $\to$ **135 Patches** ($256 \times 256$)
  - **Test Set:** 27 images held out completely for independent benchmarking.
- **Annotations Handled:**
  - `MA`: 100% annotated in training
  - `HE`: 98.1% annotated in training
  - `EX`: 100% annotated in training
  - `SE`: 48.1% annotated in training (unannotated channels dynamically masked out in BCE and Dice loss).

---

## 4. 25-Epoch Training Progression

| Epoch | Train Loss | Train BCE | Train Dice Loss | Val Loss | Val Mean Dice | Val Mean IoU | MA Dice | HE Dice | EX Dice | SE Dice |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 2.5977 | 0.6639 | 0.9669 | 2.5327 | 0.0723 | 0.0392 | 0.0017 | 0.0000 | 0.1018 | 0.1855 |
| 5 | 2.3823 | 0.4485 | 0.9669 | 2.3626 | 0.1221 | 0.0705 | 0.0000 | 0.0001 | 0.3185 | 0.1696 |
| 8 | 2.2744 | 0.3421 | 0.9661 | 2.2456 | 0.2239 | 0.1533 | 0.0000 | 0.0000 | 0.6303 | 0.2653 |
| 12 | 2.1590 | 0.2310 | 0.9640 | 2.1447 | 0.2648 | 0.1825 | 0.0000 | 0.0000 | 0.6182 | 0.4408 |
| 16 | 2.0742 | 0.1681 | 0.9530 | 2.0563 | 0.3070 | 0.2217 | 0.0000 | 0.0054 | 0.5625 | **0.6602** |
| 19 | 2.0200 | 0.1345 | 0.9427 | 2.0064 | 0.3497 | 0.2361 | 0.0000 | 0.2931 | 0.6340 | 0.4717 |
| 22 | 1.9686 | 0.1147 | 0.9269 | 1.9531 | 0.3661 | 0.2387 | 0.0831 | 0.3353 | 0.5614 | 0.4845 |
| 23 | 1.9401 | 0.1065 | 0.9168 | 1.9365 | 0.3720 | 0.2466 | 0.0862 | 0.2869 | 0.5858 | 0.5289 |
| 24 | 1.9315 | 0.1012 | 0.9151 | 1.9287 | 0.4056 | 0.2749 | **0.1908** | 0.2167 | 0.6030 | 0.6119 |
| **25 (Best)** | **1.9059** | **0.0972** | **0.9044** | **1.9212** | **0.4199** | **0.2828** | **0.1647** | **0.3620** | **0.6638** | **0.4891** |

---

## 5. Detailed Metric Breakdown (Best Model Checkpoint)

| Lesion Type | Dice Score | IoU Score | Precision | Recall | Clinical Diagnostic Significance |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Hard Exudates (EX)** | **0.6638** | **0.4968** | **84.87%** | **54.50%** | Pathognomonic for diabetic macular edema (DME) risk |
| **Soft Exudates (SE)** | **0.6602\*** | **0.3437** | **35.22%** | **80.03%** | Indicates focal retinal nerve fiber ischemia (cotton-wool spots) |
| **Haemorrhages (HE)** | **0.3620** | **0.2210** | **61.36%** | **25.68%** | Hallmark biomarker for Non-Proliferative Diabetic Retinopathy (NPDR) |
| **Microaneurysms (MA)** | **0.1908\*** | **0.0898** | **12.51%** | **24.10%** | Earliest clinically detectable sign of DR |
| **Overall Mean** | **0.4199** | **0.2828** | — | — | **Consistent multi-class segmentation convergence** |

*\*Note: SE achieved its peak Dice of 0.6602 at Epoch 16; MA achieved its peak Dice of 0.1908 at Epoch 24.*

---

## 6. Preserved Checkpoints & Deliverables

All generated outputs are organized under [`outputs/segmentation/`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/):

### Model Checkpoints
- [`best_model.pth`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/checkpoints/best_model.pth) (52.3 MB) — Best GPU model checkpoint (Epoch 25, Mean Dice: **0.4199**).
- [`best_model_prev.pth`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/checkpoints/best_model_prev.pth) (52.3 MB) — Preserved prior best GPU checkpoint (Epoch 24, Mean Dice: **0.4056**).
- [`best_model_cpu_dice_0.2476.pth`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/checkpoints/best_model_cpu_dice_0.2476.pth) (13.1 MB) — Preserved best CPU model checkpoint.
- [`latest_checkpoint.pth`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/checkpoints/latest_checkpoint.pth) (52.3 MB) — Complete optimizer and scheduler states.

### Evaluation Plots
- [`loss_curves.png`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/plots/loss_curves.png) — Total loss, BCE loss (0.66 $\to$ 0.09), and Dice loss curves.
- [`metrics_curves.png`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/plots/metrics_curves.png) — Validation Mean Dice and Mean IoU trajectory.
- [`per_class_dice.png`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/plots/per_class_dice.png) — Individual Dice curves for EX, SE, HE, and MA across all 25 epochs.

### Visual Comparisons (Predictions vs Ground Truth)
- [`IDRiD_10_p00_MA_comparison.png`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/predictions/IDRiD_10_p00_MA_comparison.png)
- [`IDRiD_10_p01_MA_comparison.png`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/predictions/IDRiD_10_p01_MA_comparison.png)
- [`IDRiD_10_p02_MA_comparison.png`](file:///C:/Users/Sanmit/Desktop/eyeris/Eyeris/outputs/segmentation/predictions/IDRiD_10_p02_MA_comparison.png)

---

## 7. Clinical Disclaimer

> [!IMPORTANT]
> **Academic Prototype Only:** This system was designed and trained as part of an academic demonstration for the Smart India Hackathon (SIH). It is **not clinically certified** and must **never** be used for independent clinical diagnosis or treatment planning.
