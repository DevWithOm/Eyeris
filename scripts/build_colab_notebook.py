"""
Script to generate the complete Google Colab notebook DR_Classification_Training.ipynb
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

cells = []

def add_markdown(source_text):
    lines = [line + "\n" for line in source_text.strip().split("\n")]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": lines
    })

def add_code(source_text):
    lines = [line + "\n" for line in source_text.strip().split("\n")]
    if lines:
        lines[-1] = lines[-1].rstrip("\n")
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines
    })

# -----------------------------------------------------------------------------
# CELL 0: TITLE & ROADMAP
# -----------------------------------------------------------------------------
add_markdown("""# 🩺 Diabetic Retinopathy Classification with PyTorch & EfficientNet-B0
### An End-to-End Deep Learning Pipeline for APTOS 2019 with IDRiD External Validation

---

## 📌 Project Overview
Diabetic Retinopathy (DR) is an eye disease caused by complications of diabetes that damages retinal blood vessels and is a leading cause of blindness worldwide. This notebook implements an end-to-end, reproducible deep learning pipeline using **PyTorch** and **EfficientNet-B0** to classify digital fundus photographs into 5 clinical grades defined by the International Clinical Diabetic Retinopathy Disease Severity Scale:
- **Grade 0**: No DR (Healthy retina)
- **Grade 1**: Mild non-proliferative DR (Microaneurysms only)
- **Grade 2**: Moderate non-proliferative DR (More than microaneurysms, but less than severe)
- **Grade 3**: Severe non-proliferative DR (Cotton wool spots, venous beading, severe intraretinal microvascular abnormalities)
- **Grade 4**: Proliferative DR (Neovascularization, vitreous/preretinal hemorrhage)

In addition to 5-class multi-class grading, the notebook evaluates clinical **Referable Diabetic Retinopathy** (Grades 0–1 vs Grades 2–4), computing diagnostic **Sensitivity** and **Specificity**.

---

## 📋 Recommended Execution Order & Cell Roadmap

Follow this sequential cell execution order for a clean, reproducible run:

| Step | Cell Name / Section | Purpose | Expected Output |
|:---:|:---|:---|:---|
| **1** | **Section 1: Hardware & Environment Diagnostics** | Checks Colab vs local, detects GPU (T4/V100/A100), sets deterministic seeds. | GPU device name & VRAM printed. |
| **2** | **Section 2: Dependencies Installation** | Installs `timm`, `scikit-learn`, `seaborn` and imports PyTorch & CV libraries. | Import confirmation. |
| **3** | **Section 3: Google Drive & Configurable Paths** | Mounts Google Drive (`/content/drive`) and configures data/output directories. | Directory structure verified. |
| **4** | **Section 4: Hyperparameters & Configuration** | Central dictionary for batch size, LR, epochs, image size, and referable threshold. | Config parameters printed. |
| **5** | **Section 5: APTOS Dataset Inspection & Validation** | Validates CSV columns, checks missing values, verifies image files, plots class distribution. | Class counts & distribution plot. |
| **6** | **Section 6: Visualizing Representative Retinal Images** | Displays 5 fundus images across DR grades 0 to 4. | 1x5 image grid. |
| **7** | **Section 7: Retinal Preprocessing & Border Cropping** | Auto-crops black borders around fundus circle, demonstrates on samples. | 2x4 before/after comparison. |
| **8** | **Section 8: Stratified Train / Val / Test Split** | Stratified 70/15/15 splitting, saves locked split manifests to `data/splits/`. | Verification table & saved CSVs. |
| **9** | **Section 9: PyTorch Datasets & DataLoaders** | Implements `RetinopathyDataset`, applies augmentations, creates DataLoaders. | Batch shape confirmation. |
| **10** | **Section 10: EfficientNet-B0 Architecture** | Loads pretrained EfficientNet-B0, customizes classifier head, sets AdamW & Scheduler. | Model parameter summary. |
| **11** | **Section 11: Model Training with Validation Checkpointing** | Runs training loop; tracks Loss, Acc, Macro F1; saves `best_model.pth` on highest Val F1. | Epoch progress & checkpoint saved. |
| **12** | **Section 12: Training Convergence Curves** | Plots Loss, Accuracy, and Macro F1 curves vs epochs to assess generalization. | `learning_curves.png`. |
| **13** | **Section 13: Final Evaluation on Locked Test Set** | Loads `best_model.pth` and evaluates unseen test split without data leakage. | Test Accuracy & Classification Report. |
| **14** | **Section 14: Confusion Matrix & Referable DR Metrics** | Computes 5-class confusion matrix, Referable DR Sensitivity, Specificity, and JSON report. | Confusion matrix plot & report. |
| **15** | **Section 15: Prediction Function & Visual Showcase** | Predicts single images or PIL inputs with colored probability bars and clinical referral text. | Sample visual predictions. |
| **16** | **Section 16: IDRiD Label Verification & Compatibility Check** | Checks IDRiD folder structure, cleans CSV columns, verifies 0–4 scale and image file presence. | Compatibility status report. |
| **17** | **Section 17: IDRiD Zero-Shot External Evaluation** | Tests domain transfer on IDRiD, plots confusion matrix, compares in-domain vs out-of-domain. | Domain generalization table. |
| **18** | **Section 18: Artifact Audit & Drive Sync** | Audits all saved models, plots, reports, and manifests on Google Drive. | File list with sizes. |

> 💡 **Google Colab Tip**: To enable GPU acceleration in Colab, navigate to:  
> `Runtime` ➡️ `Change runtime type` ➡️ Under *Hardware accelerator*, select **T4 GPU** ➡️ Click **Save**.""")

# -----------------------------------------------------------------------------
# SECTION 1
# -----------------------------------------------------------------------------
add_markdown("""## 1. Hardware & Environment Diagnostics
Verifies whether the notebook is executing in Google Colab or locally, detects GPU hardware availability, and configures reproducible random seeds.""")

add_code("""# =============================================================================
# 1. HARDWARE & ENVIRONMENT DIAGNOSTICS
# =============================================================================
import os
import sys
import random
import numpy as np
import torch

# Detect environment
try:
    import google.colab
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

print("=" * 65)
print(f"Execution Environment : {'Google Colab' if IN_COLAB else 'Local / Custom'}")
print(f"Python Version        : {sys.version.split()[0]}")
print(f"PyTorch Version       : {torch.__version__}")

# GPU Check & Device Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Active Device         : {device}")

if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"GPU Model             : {gpu_name}")
    print(f"Total GPU VRAM        : {gpu_vram:.2f} GB")
    print(f"CUDA Capability       : {torch.cuda.get_device_capability(0)}")
else:
    print("⚠️ WARNING: No CUDA GPU detected! Training on CPU will be slow.")
    if IN_COLAB:
        print("👉 In Google Colab, enable GPU: Runtime -> Change runtime type -> Hardware accelerator: T4 GPU")
print("=" * 65)

# Set random seeds for reproducibility
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

set_seed(42)
print("✅ Reproducibility seed set to 42.")""")

# -----------------------------------------------------------------------------
# SECTION 2
# -----------------------------------------------------------------------------
add_markdown("""## 2. Dependencies Installation & Imports
Ensures required packages (`timm`, `scikit-learn`, `seaborn`, `pillow`) are installed and imports core libraries.""")

add_code("""# =============================================================================
# 2. DEPENDENCIES INSTALLATION & IMPORTS
# =============================================================================
import subprocess
import sys

# Ensure required packages are installed
required_pkgs = ["timm", "scikit-learn", "pandas", "pillow", "matplotlib", "seaborn"]
missing_pkgs = []
for pkg in required_pkgs:
    try:
        __import__(pkg)
    except ImportError:
        missing_pkgs.append(pkg)

if missing_pkgs:
    print(f"Installing missing packages: {missing_pkgs}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + missing_pkgs)
    print("Packages installed successfully.")

import time
import json
from pathlib import Path
from PIL import Image

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from IPython.display import display
except ImportError:
    def display(*args):
        for a in args:
            print(a)

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
import timm

print("✅ All computer vision and deep learning packages imported successfully!")""")

# -----------------------------------------------------------------------------
# SECTION 3
# -----------------------------------------------------------------------------
add_markdown("""## 3. Google Drive Mounting & Configurable Paths
Mounts Google Drive (when running in Colab) and configures paths for datasets, model checkpoints, plots, and metric reports.""")

add_code("""# =============================================================================
# 3. GOOGLE DRIVE MOUNTING & CONFIGURABLE PATHS
# =============================================================================
if IN_COLAB:
    from google.colab import drive
    if not os.path.exists("/content/drive/MyDrive"):
        print("Mounting Google Drive to /content/drive...")
        drive.mount("/content/drive")
    else:
        print("Google Drive is already mounted.")

# Determine Project Root Directory
# Users can modify this path to point to their exact Google Drive folder
if IN_COLAB:
    DRIVE_CANDIDATE = Path("/content/drive/MyDrive/DR_Classification_Project_Template")
    if DRIVE_CANDIDATE.exists():
        PROJECT_ROOT = DRIVE_CANDIDATE
    else:
        PROJECT_ROOT = Path("/content")
else:
    PROJECT_ROOT = Path(".").resolve()

print(f"Base Project Root: {PROJECT_ROOT}")

# Configurable Path Dictionary
PATHS = {
    # APTOS dataset paths
    "aptos_csv": PROJECT_ROOT / "data" / "raw" / "aptos" / "train.csv",
    "aptos_images": PROJECT_ROOT / "data" / "raw" / "aptos" / "train_images",

    # IDRiD external dataset paths
    "idrid_test_csv": (
        PROJECT_ROOT / "data" / "raw" / "idrid" / "disease_grading" /
        "2. Groundtruths" / "b. IDRiD_Disease Grading_Testing Labels.csv"
    ),
    "idrid_test_images": (
        PROJECT_ROOT / "data" / "raw" / "idrid" / "disease_grading" /
        "1. Original Images" / "b. Testing Set"
    ),
    "idrid_train_csv": (
        PROJECT_ROOT / "data" / "raw" / "idrid" / "disease_grading" /
        "2. Groundtruths" / "a. IDRiD_Disease Grading_Training Labels.csv"
    ),
    "idrid_train_images": (
        PROJECT_ROOT / "data" / "raw" / "idrid" / "disease_grading" /
        "1. Original Images" / "a. Training Set"
    ),

    # Output directories (Weights, Plots, Reports, Splits)
    "splits_dir": PROJECT_ROOT / "data" / "splits",
    "checkpoints_dir": PROJECT_ROOT / "checkpoints",
    "plots_dir": PROJECT_ROOT / "outputs" / "plots",
    "reports_dir": PROJECT_ROOT / "outputs" / "reports",
}

# Auto-create output directories if missing
for dir_key in ["splits_dir", "checkpoints_dir", "plots_dir", "reports_dir"]:
    PATHS[dir_key].mkdir(parents=True, exist_ok=True)
    print(f"Directory ready: {PATHS[dir_key]}")""")

# -----------------------------------------------------------------------------
# SECTION 4
# -----------------------------------------------------------------------------
add_markdown("""## 4. Hyperparameters & Configuration
Central configuration for reproducible model training and evaluation.""")

add_code("""# =============================================================================
# 4. HYPERPARAMETERS & CONFIGURATION
# =============================================================================
CONFIG = {
    "seed": 42,
    "num_classes": 5,
    "class_names": [
        "0 - No DR",
        "1 - Mild",
        "2 - Moderate",
        "3 - Severe",
        "4 - Proliferative DR"
    ],
    "class_names_short": ["No DR", "Mild", "Moderate", "Severe", "Proliferative"],

    # Preprocessing
    "image_size": 224,        # Standard input resolution for EfficientNet-B0
    "crop_borders": True,     # Automatically crop uninformative black margins

    # Model & Training
    "model_name": "efficientnet_b0",
    "pretrained": True,
    "batch_size": 16,         # Safe for Colab T4 GPU VRAM
    "num_workers": 2 if IN_COLAB else 0,  # 2 in Colab Linux, 0 on Windows
    "epochs": 10,
    "learning_rate": 1e-4,
    "weight_decay": 1e-4,

    # Clinical Referable DR threshold
    # Grades 0-1 = Non-Referable (0)
    # Grades 2-4 = Referable DR (1)
    "referable_threshold": 2,

    # Stratified Split Ratios
    "train_ratio": 0.70,
    "val_ratio": 0.15,
    "test_ratio": 0.15,
}

print("Active Configuration Parameters:")
for k, v in CONFIG.items():
    print(f"  {k:20s}: {v}")""")

# -----------------------------------------------------------------------------
# SECTION 5
# -----------------------------------------------------------------------------
add_markdown("""## 5. APTOS Dataset Inspection & Validation
Inspects `train.csv`, checks column names, drops missing values, verifies image file presence on disk, and plots the class distribution.""")

add_code("""# =============================================================================
# 5. APTOS DATASET INSPECTION & INTEGRITY VALIDATION
# =============================================================================
aptos_csv_path = PATHS["aptos_csv"]
aptos_img_dir = PATHS["aptos_images"]

print(f"Checking APTOS train.csv at: {aptos_csv_path}")
assert aptos_csv_path.exists(), (
    f"❌ APTOS CSV not found at {aptos_csv_path}!\\n"
    f"Please upload train.csv to data/raw/aptos/ or update PATHS['aptos_csv']."
)
assert aptos_img_dir.exists(), (
    f"❌ APTOS train_images directory not found at {aptos_img_dir}!\\n"
    f"Please extract training images to data/raw/aptos/train_images/."
)

df_aptos = pd.read_csv(aptos_csv_path)
print(f"✅ APTOS CSV loaded successfully: {len(df_aptos)} total rows.")
print("Sample rows:")
display(df_aptos.head())

# Check required column names
assert "id_code" in df_aptos.columns, "Missing 'id_code' column in CSV!"
assert "diagnosis" in df_aptos.columns, "Missing 'diagnosis' column in CSV!"

# Check for missing values / NaNs
null_counts = df_aptos[["id_code", "diagnosis"]].isnull().sum()
print("\\nMissing value check:")
print(null_counts)
if null_counts.any():
    print("⚠️ Dropping rows with null values...")
    df_aptos = df_aptos.dropna(subset=["id_code", "diagnosis"]).reset_index(drop=True)

# Verify physical image existence on disk
print("\\nVerifying image file existence on disk...")
valid_rows = []
missing_count = 0

for _, row in df_aptos.iterrows():
    img_candidate = aptos_img_dir / f"{row['id_code']}.png"
    if img_candidate.exists():
        valid_rows.append(row)
    else:
        missing_count += 1

if missing_count > 0:
    print(f"⚠️ Warning: {missing_count} referenced images not found in {aptos_img_dir}!")
    df_aptos = pd.DataFrame(valid_rows).reset_index(drop=True)
    print(f"Proceeding with {len(df_aptos)} verified images.")
else:
    print(f"✅ All {len(df_aptos)} referenced images verified on disk!")

# Class distribution analysis
dist = df_aptos["diagnosis"].value_counts().sort_index()
dist_df = pd.DataFrame({
    "Grade": dist.index,
    "Diagnosis": [CONFIG["class_names"][i] for i in dist.index],
    "Count": dist.values,
    "Percentage": [f"{c / len(df_aptos) * 100:.2f}%" for c in dist.values]
})
print("\\nAPTOS Diagnosis Distribution:")
display(dist_df)

# Plot class distribution bar chart
plt.figure(figsize=(9, 4.5))
bars = plt.bar(
    CONFIG["class_names_short"],
    dist.values,
    color=["#2b5c8f", "#3690c0", "#67a9cf", "#02818a", "#e41a1c"]
)
plt.title("APTOS 2019 Diabetic Retinopathy Class Distribution", fontsize=13, fontweight="bold")
plt.xlabel("DR Severity Grade", fontsize=11)
plt.ylabel("Number of Retinal Images", fontsize=11)
plt.grid(axis="y", linestyle="--", alpha=0.5)

for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 15,
        f"{yval}\\n({yval / len(df_aptos) * 100:.1f}%)",
        ha="center",
        va="bottom",
        fontsize=9
    )

plt.tight_layout()
plot_path = PATHS["plots_dir"] / "aptos_class_distribution.png"
plt.savefig(plot_path, dpi=200)
plt.show()
print(f"Saved distribution plot to: {plot_path}")""")

# -----------------------------------------------------------------------------
# SECTION 6
# -----------------------------------------------------------------------------
add_markdown("""## 6. Visualizing Representative Retinal Images
Displays sample fundus images across all 5 Diabetic Retinopathy grades.""")

add_code("""# =============================================================================
# 6. VISUALIZING REPRESENTATIVE RETINAL IMAGES ACROSS GRADES
# =============================================================================
fig, axes = plt.subplots(1, 5, figsize=(18, 4.5))
fig.suptitle("Representative APTOS Retinal Fundus Images Across 5 DR Grades", fontsize=14, fontweight="bold")

for grade in range(5):
    sample_rows = df_aptos[df_aptos["diagnosis"] == grade]
    if len(sample_rows) > 0:
        sample = sample_rows.iloc[0]
        img_path = aptos_img_dir / f"{sample['id_code']}.png"
        img = Image.open(img_path)

        axes[grade].imshow(img)
        axes[grade].set_title(
            f"{CONFIG['class_names'][grade]}\\nID: {sample['id_code']}\\nSize: {img.size}",
            fontsize=10
        )
    axes[grade].axis("off")

plt.tight_layout()
plt.show()""")

# -----------------------------------------------------------------------------
# SECTION 7
# -----------------------------------------------------------------------------
add_markdown("""## 7. Retinal Preprocessing & Border Cropping
Detects the fundus aperture and removes black borders, focusing the CNN on diagnostic retinal tissue.""")

add_code("""# =============================================================================
# 7. RETINAL FUNDUS PREPROCESSING: BORDER CROPPING
# =============================================================================
def crop_fundus_borders(image: Image.Image, tol: int = 10) -> Image.Image:
    \"\"\"
    Detects and crops black outer margins from retinal fundus photographs.
    Finds non-dark bounding box pixels and crops, with fallback if degenerate.
    \"\"\"
    np_img = np.array(image)
    if np_img.ndim == 2:
        mask = np_img > tol
    else:
        mask = np_img.max(axis=2) > tol

    if not np.any(mask):
        return image

    row_nonzero = np.where(mask.any(axis=1))[0]
    col_nonzero = np.where(mask.any(axis=0))[0]

    if len(row_nonzero) == 0 or len(col_nonzero) == 0:
        return image

    ymin, ymax = row_nonzero[0], row_nonzero[-1]
    xmin, xmax = col_nonzero[0], col_nonzero[-1]

    # Ensure crop is not trivial / collapsed
    if (ymax - ymin < 50) or (xmax - xmin < 50):
        return image

    return image.crop((xmin, ymin, xmax, ymax))

# Visual demonstration of border cropping on 4 sample images
fig, axes = plt.subplots(2, 4, figsize=(16, 7.5))
fig.suptitle("Retinal Preprocessing: Original vs Border-Cropped & Resized (224x224)", fontsize=14, fontweight="bold")

sample_sub = df_aptos.sample(4, random_state=CONFIG["seed"])
for col_idx, (_, row) in enumerate(sample_sub.iterrows()):
    orig_img = Image.open(aptos_img_dir / f"{row['id_code']}.png")
    cropped_img = crop_fundus_borders(orig_img)
    resized_img = cropped_img.resize((CONFIG["image_size"], CONFIG["image_size"]), Image.BILINEAR)

    # Row 0: Original
    axes[0, col_idx].imshow(orig_img)
    axes[0, col_idx].set_title(f"Original ({orig_img.size[0]}x{orig_img.size[1]})\\nGrade: {row['diagnosis']}", fontsize=10)
    axes[0, col_idx].axis("off")

    # Row 1: Cropped & Resized
    axes[1, col_idx].imshow(resized_img)
    axes[1, col_idx].set_title(f"Cropped & Resized (224x224)\\nCrop BBox: {cropped_img.size}", fontsize=10)
    axes[1, col_idx].axis("off")

plt.tight_layout()
crop_demo_path = PATHS["plots_dir"] / "crop_comparison.png"
plt.savefig(crop_demo_path, dpi=200)
plt.show()
print(f"Saved preprocessing demonstration plot to: {crop_demo_path}")""")

# -----------------------------------------------------------------------------
# SECTION 8
# -----------------------------------------------------------------------------
add_markdown("""## 8. Stratified Train / Validation / Test Splitting
Splits dataset into 70% Train, 15% Validation, and 15% Test partitions using stratified sampling. Saves split manifests to `data/splits/` and locks the test set.""")

add_code("""# =============================================================================
# 8. STRATIFIED TRAIN / VALIDATION / TEST SPLIT
# =============================================================================
train_ratio = CONFIG["train_ratio"]
val_ratio = CONFIG["val_ratio"]
test_ratio = CONFIG["test_ratio"]

# Step 1: Split into Train (70%) and Temp (30%)
temp_ratio = val_ratio + test_ratio
df_train, df_temp = train_test_split(
    df_aptos,
    test_size=temp_ratio,
    stratify=df_aptos["diagnosis"],
    random_state=CONFIG["seed"]
)

# Step 2: Split Temp into Validation (15%) and Test (15%)
val_relative_ratio = val_ratio / temp_ratio
df_val, df_test = train_test_split(
    df_temp,
    test_size=(1.0 - val_relative_ratio),
    stratify=df_temp["diagnosis"],
    random_state=CONFIG["seed"]
)

# Reset indices
df_train = df_train.reset_index(drop=True)
df_val = df_val.reset_index(drop=True)
df_test = df_test.reset_index(drop=True)

# Save split manifests
train_split_path = PATHS["splits_dir"] / "train_split.csv"
val_split_path = PATHS["splits_dir"] / "val_split.csv"
test_split_path = PATHS["splits_dir"] / "test_split.csv"

df_train.to_csv(train_split_path, index=False)
df_val.to_csv(val_split_path, index=False)
df_test.to_csv(test_split_path, index=False)

print(f"Saved split manifests to {PATHS['splits_dir']}:")
print(f"  Train : {len(df_train)} rows ({len(df_train) / len(df_aptos) * 100:.1f}%)")
print(f"  Val   : {len(df_val)} rows ({len(df_val) / len(df_aptos) * 100:.1f}%)")
print(f"  Test  : {len(df_test)} rows ({len(df_test) / len(df_aptos) * 100:.1f}%) [LOCKED]")

# Verification of zero identifier overlap and complete class representation
set_train = set(df_train["id_code"])
set_val = set(df_val["id_code"])
set_test = set(df_test["id_code"])

assert len(set_train & set_val) == 0, "❌ Overlap between Train and Val splits!"
assert len(set_train & set_test) == 0, "❌ Overlap between Train and Test splits!"
assert len(set_val & set_test) == 0, "❌ Overlap between Val and Test splits!"
print("✅ Verified: Exactly 0 overlapping identifiers across Train, Val, and Test splits.")

# Verification of class stratification across splits
split_check = pd.DataFrame({
    "Grade": range(5),
    "Diagnosis": CONFIG["class_names_short"],
    "Train_Count": df_train["diagnosis"].value_counts().sort_index().values,
    "Train_%": (df_train["diagnosis"].value_counts().sort_index().values / len(df_train) * 100).round(2),
    "Val_Count": df_val["diagnosis"].value_counts().sort_index().values,
    "Val_%": (df_val["diagnosis"].value_counts().sort_index().values / len(df_val) * 100).round(2),
    "Test_Count": df_test["diagnosis"].value_counts().sort_index().values,
    "Test_%": (df_test["diagnosis"].value_counts().sort_index().values / len(df_test) * 100).round(2),
})

print("\\nStratification Verification Table:")
display(split_check)""")

# -----------------------------------------------------------------------------
# SECTION 9
# -----------------------------------------------------------------------------
add_markdown("""## 9. PyTorch Dataset & DataLoaders
Builds `RetinopathyDataset` with data augmentation for training (random flips, rotation, jitter) and deterministic normalization for validation/testing.""")

add_code("""# =============================================================================
# 9. PYTORCH DATASET & DATALOADERS
# =============================================================================
NORMALIZE = transforms.Normalize(
    mean=[0.485, 0.456, 0.406],
    std=[0.229, 0.224, 0.225]
)

# Training transforms with clinically sensible data augmentation
train_transforms = transforms.Compose([
    transforms.Resize((CONFIG["image_size"], CONFIG["image_size"])),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.5),
    transforms.RandomRotation(degrees=20),
    transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
    transforms.ToTensor(),
    NORMALIZE
])

# Validation & Test transforms (strictly deterministic)
eval_transforms = transforms.Compose([
    transforms.Resize((CONFIG["image_size"], CONFIG["image_size"])),
    transforms.ToTensor(),
    NORMALIZE
])

class RetinopathyDataset(Dataset):
    \"\"\"Custom PyTorch Dataset for Diabetic Retinopathy Fundus Images.\"\"\"
    def __init__(
        self,
        df: pd.DataFrame,
        img_dir: Path,
        transform=None,
        crop_borders: bool = True,
        img_col: str = "id_code",
        label_col: str = "diagnosis",
        img_ext: str = ".png"
    ):
        self.df = df.reset_index(drop=True)
        self.img_dir = Path(img_dir)
        self.transform = transform
        self.crop_borders = crop_borders
        self.img_col = img_col
        self.label_col = label_col
        self.img_ext = img_ext

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_name = str(row[self.img_col])

        # Robustly resolve image file path with candidate extensions
        img_path = self.img_dir / img_name
        if not img_path.exists():
            for ext in [self.img_ext, ".png", ".jpg", ".JPG", ".jpeg"]:
                candidate = self.img_dir / f"{img_name}{ext}"
                if candidate.exists():
                    img_path = candidate
                    break

        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Failed to read image {img_path}: {e}")

        if self.crop_borders:
            image = crop_fundus_borders(image)

        if self.transform is not None:
            image = self.transform(image)

        label = int(row[self.label_col])
        return image, torch.tensor(label, dtype=torch.long), img_name

# Initialize Datasets
train_dataset = RetinopathyDataset(df_train, aptos_img_dir, transform=train_transforms, crop_borders=CONFIG["crop_borders"])
val_dataset = RetinopathyDataset(df_val, aptos_img_dir, transform=eval_transforms, crop_borders=CONFIG["crop_borders"])
test_dataset = RetinopathyDataset(df_test, aptos_img_dir, transform=eval_transforms, crop_borders=CONFIG["crop_borders"])

# Create DataLoaders
pin_memory = torch.cuda.is_available()
train_loader = DataLoader(
    train_dataset,
    batch_size=CONFIG["batch_size"],
    shuffle=True,
    num_workers=CONFIG["num_workers"],
    pin_memory=pin_memory
)
val_loader = DataLoader(
    val_dataset,
    batch_size=CONFIG["batch_size"],
    shuffle=False,
    num_workers=CONFIG["num_workers"],
    pin_memory=pin_memory
)
test_loader = DataLoader(
    test_dataset,
    batch_size=CONFIG["batch_size"],
    shuffle=False,
    num_workers=CONFIG["num_workers"],
    pin_memory=pin_memory
)

sample_batch, sample_labels, sample_ids = next(iter(train_loader))
print("DataLoaders successfully configured:")
print(f"  Train Loader: {len(train_loader)} batches ({len(train_dataset)} samples)")
print(f"  Val Loader  : {len(val_loader)} batches ({len(val_dataset)} samples)")
print(f"  Test Loader : {len(test_loader)} batches ({len(test_dataset)} samples)")
print(f"  Sample batch tensor shape: {sample_batch.shape}")
print(f"  Sample label batch shape : {sample_labels.shape}")""")

# -----------------------------------------------------------------------------
# SECTION 10
# -----------------------------------------------------------------------------
add_markdown("""## 10. Model Architecture: EfficientNet-B0
Loads pretrained EfficientNet-B0, modifies the final linear classifier with dropout for 5-class grading, and configures AdamW optimizer with ReduceLROnPlateau scheduler.""")

add_code("""# =============================================================================
# 10. MODEL ARCHITECTURE: EfficientNet-B0
# =============================================================================
def build_efficientnet_b0(num_classes: int = 5, pretrained: bool = True):
    \"\"\"Builds EfficientNet-B0 and adapts the classifier head for 5 DR grades.\"\"\"
    try:
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features=in_features, out_features=num_classes)
        )
        print("Loaded torchvision EfficientNet-B0 with ImageNet pretrained weights.")
    except Exception as e:
        print(f"Falling back to timm EfficientNet-B0 ({e})...")
        model = timm.create_model("efficientnet_b0", pretrained=pretrained, num_classes=num_classes)
        print("Loaded timm EfficientNet-B0.")
    return model

model = build_efficientnet_b0(num_classes=CONFIG["num_classes"]).to(device)

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Total Model Parameters    : {total_params:,}")
print(f"Trainable Model Parameters: {trainable_params:,}")

# Loss with Balanced Class Weights (Handling Class Imbalance), Optimizer, and Scheduler
train_counts = df_train["diagnosis"].value_counts().sort_index().values
total_train = len(df_train)
raw_weights = total_train / (CONFIG["num_classes"] * train_counts)
normalized_weights = torch.tensor(raw_weights / raw_weights.mean(), dtype=torch.float32).to(device)

print("\nComputed Balanced Class Weights (CrossEntropyLoss):")
for idx, w in enumerate(normalized_weights.cpu().numpy()):
    print(f"  Grade {idx} ({CONFIG['class_names_short'][idx]}): {w:.4f}")

criterion = nn.CrossEntropyLoss(weight=normalized_weights)
optimizer = optim.AdamW(
    model.parameters(),
    lr=CONFIG["learning_rate"],
    weight_decay=CONFIG["weight_decay"]
)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.5,
    patience=2,
    min_lr=1e-6
)

print(f"\nOptimizer : AdamW (lr={CONFIG['learning_rate']}, weight_decay={CONFIG['weight_decay']})")
print("Criterion : CrossEntropyLoss (with balanced class weights)")
print("Scheduler : ReduceLROnPlateau (monitoring Validation Macro F1)")""")

# -----------------------------------------------------------------------------
# SECTION 11
# -----------------------------------------------------------------------------
add_markdown("""## 11. Model Training with Validation Checkpointing
Iterates through epochs, computes Train & Validation metrics, and saves the best model checkpoint weights on highest **Validation Macro F1** to prevent overfitting.""")

add_code("""# =============================================================================
# 11. MODEL TRAINING WITH VALIDATION-BASED CHECKPOINT SELECTION
# =============================================================================
def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    all_preds, all_labels = [], []

    for images, labels, _ in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        preds = torch.argmax(outputs, dim=1).detach().cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())

    epoch_loss = running_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    return epoch_loss, epoch_acc

def evaluate_model(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds, all_labels = [], []

    with torch.no_grad():
        for images, labels, _ in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    eval_loss = running_loss / len(loader.dataset)
    eval_acc = accuracy_score(all_labels, all_preds)
    eval_macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    return eval_loss, eval_acc, eval_macro_f1, all_labels, all_preds

history = {
    "train_loss": [],
    "train_acc": [],
    "val_loss": [],
    "val_acc": [],
    "val_macro_f1": [],
    "lr": []
}

best_val_macro_f1 = -1.0
best_model_path = PATHS["checkpoints_dir"] / "best_model.pth"
best_checkpoint_path = PATHS["checkpoints_dir"] / "best_checkpoint.tar"
last_model_path = PATHS["checkpoints_dir"] / "last_model.pth"

print("=" * 82)
print(f"{'Epoch':^6} | {'Train Loss':^10} | {'Train Acc':^10} | {'Val Loss':^10} | {'Val Acc':^10} | {'Val Macro F1':^12} | {'Time':^8}")
print("=" * 82)

num_epochs = CONFIG["epochs"]
start_train_time = time.time()

for epoch in range(1, num_epochs + 1):
    epoch_start = time.time()

    train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
    val_loss, val_acc, val_f1, _, _ = evaluate_model(model, val_loader, criterion, device)

    current_lr = optimizer.param_groups[0]["lr"]

    history["train_loss"].append(train_loss)
    history["train_acc"].append(train_acc)
    history["val_loss"].append(val_loss)
    history["val_acc"].append(val_acc)
    history["val_macro_f1"].append(val_f1)
    history["lr"].append(current_lr)

    scheduler.step(val_f1)

    epoch_time = time.time() - epoch_start
    print(f"{epoch:^6d} | {train_loss:^10.4f} | {train_acc * 100:^9.2f}% | {val_loss:^10.4f} | {val_acc * 100:^9.2f}% | {val_f1:^12.4f} | {epoch_time:^7.1f}s", end="")

    if val_f1 > best_val_macro_f1:
        best_val_macro_f1 = val_f1
        torch.save(model.state_dict(), best_model_path)
        torch.save({
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "val_macro_f1": val_f1,
            "val_loss": val_loss,
            "config": CONFIG
        }, best_checkpoint_path)
        print(f"  🌟 [BEST CHECKPOINT SAVED: F1={val_f1:.4f}]")
    else:
        print("")

torch.save(model.state_dict(), last_model_path)
total_train_elapsed = time.time() - start_train_time

print("=" * 82)
print(f"✅ Training completed in {total_train_elapsed / 60:.2f} minutes.")
print(f"⭐ Best Validation Macro F1 : {best_val_macro_f1:.4f}")
print(f"💾 Best Model Weights Saved : {best_model_path}")""")

# -----------------------------------------------------------------------------
# SECTION 12
# -----------------------------------------------------------------------------
add_markdown("""## 12. Training Convergence & Learning Curves
Plots training and validation loss, accuracy, and macro F1 curves to verify convergence and check for overfitting.""")

add_code("""# =============================================================================
# 12. TRAINING CONVERGENCE & LEARNING CURVES
# =============================================================================
epochs_range = range(1, len(history["train_loss"]) + 1)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("EfficientNet-B0 Training & Validation Curves (APTOS 2019)", fontsize=14, fontweight="bold")

# Loss Curve
axes[0].plot(epochs_range, history["train_loss"], "o-", label="Train Loss", color="#2b5c8f", lw=2)
axes[0].plot(epochs_range, history["val_loss"], "s--", label="Val Loss", color="#e41a1c", lw=2)
axes[0].set_title("Cross-Entropy Loss", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Epoch", fontsize=10)
axes[0].set_ylabel("Loss", fontsize=10)
axes[0].legend()
axes[0].grid(True, linestyle="--", alpha=0.5)

# Accuracy Curve
axes[1].plot(epochs_range, [a * 100 for a in history["train_acc"]], "o-", label="Train Acc", color="#2b5c8f", lw=2)
axes[1].plot(epochs_range, [a * 100 for a in history["val_acc"]], "s--", label="Val Acc", color="#238b45", lw=2)
axes[1].set_title("Accuracy (%)", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Epoch", fontsize=10)
axes[1].set_ylabel("Accuracy (%)", fontsize=10)
axes[1].legend()
axes[1].grid(True, linestyle="--", alpha=0.5)

# Macro F1 Curve
axes[2].plot(epochs_range, history["val_macro_f1"], "D-", label="Val Macro F1", color="#6a51a3", lw=2)
best_ep = np.argmax(history["val_macro_f1"]) + 1
axes[2].axvline(x=best_ep, color="r", linestyle=":", label=f"Best Ep {best_ep} ({best_val_macro_f1:.3f})")
axes[2].set_title("Validation Macro F1 (Checkpoint Metric)", fontsize=12, fontweight="bold")
axes[2].set_xlabel("Epoch", fontsize=10)
axes[2].set_ylabel("Macro F1", fontsize=10)
axes[2].legend()
axes[2].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
curves_path = PATHS["plots_dir"] / "learning_curves.png"
plt.savefig(curves_path, dpi=200)
plt.show()
print(f"Saved learning curves plot to: {curves_path}")""")

# -----------------------------------------------------------------------------
# SECTION 13
# -----------------------------------------------------------------------------
add_markdown("""## 13. Final Evaluation on Locked Test Set
Loads `best_model.pth` and evaluates the strictly held-out test split, reporting overall accuracy, macro/weighted F1, and per-class precision and recall.""")

add_code("""# =============================================================================
# 13. FINAL TEST EVALUATION (ON LOCKED TEST SET)
# =============================================================================
print("Loading best checkpoint weights for final evaluation on locked test split...")
model.load_state_dict(torch.load(best_model_path, map_location=device))
model.eval()

test_preds = []
test_labels = []
test_probs = []

with torch.no_grad():
    for images, labels, _ in test_loader:
        images = images.to(device)
        outputs = model(images)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()
        preds = np.argmax(probs, axis=1)

        test_probs.extend(probs)
        test_preds.extend(preds)
        test_labels.extend(labels.numpy())

test_preds = np.array(test_preds)
test_labels = np.array(test_labels)
test_probs = np.array(test_probs)

# Metric computations
test_acc = accuracy_score(test_labels, test_preds)
test_macro_f1 = f1_score(test_labels, test_preds, average="macro", zero_division=0)
test_weighted_f1 = f1_score(test_labels, test_preds, average="weighted", zero_division=0)
test_macro_prec = precision_score(test_labels, test_preds, average="macro", zero_division=0)
test_macro_rec = recall_score(test_labels, test_preds, average="macro", zero_division=0)

print("=" * 65)
print("FINAL TEST EVALUATION RESULTS (LOCKED APTOS TEST SET)")
print("=" * 65)
print(f"Total Test Images Evaluated : {len(test_labels)}")
print(f"Overall Accuracy            : {test_acc * 100:.2f}%")
print(f"Macro Precision             : {test_macro_prec:.4f}")
print(f"Macro Recall                : {test_macro_rec:.4f}")
print(f"Macro F1 Score              : {test_macro_f1:.4f}")
print(f"Weighted F1 Score           : {test_weighted_f1:.4f}")
print("=" * 65)

# Detailed per-class classification report
cls_report = classification_report(
    test_labels,
    test_preds,
    target_names=CONFIG["class_names"],
    output_dict=True,
    zero_division=0
)
print("\\nPer-Class Precision, Recall, and F1-Score:")
print(classification_report(test_labels, test_preds, target_names=CONFIG["class_names"], zero_division=0))""")

# -----------------------------------------------------------------------------
# SECTION 14
# -----------------------------------------------------------------------------
add_markdown("""## 14. Confusion Matrix & Referable DR Clinical Metrics
Generates the 5-class confusion matrix and evaluates binary Referable DR (Grades 0–1 vs 2–4), computing clinical **Sensitivity** and **Specificity**.""")

add_code("""# =============================================================================
# 14. CONFUSION MATRIX & REFERABLE DR CLINICAL METRICS
# =============================================================================
# 1. Five-Class Confusion Matrix Plot
cm = confusion_matrix(test_labels, test_preds, labels=range(5))

plt.figure(figsize=(8, 6.5))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=CONFIG["class_names_short"],
    yticklabels=CONFIG["class_names_short"],
    cbar=True
)
plt.title("5-Class DR Confusion Matrix on Locked APTOS Test Set", fontsize=13, fontweight="bold")
plt.xlabel("Predicted DR Grade", fontsize=11)
plt.ylabel("Ground Truth DR Grade", fontsize=11)
plt.tight_layout()
cm_plot_path = PATHS["plots_dir"] / "confusion_matrix_test.png"
plt.savefig(cm_plot_path, dpi=200)
plt.show()
print(f"Saved confusion matrix plot to: {cm_plot_path}")

# 2. Clinical Referable DR Evaluation
# Standard: Grade 0 (No DR) & 1 (Mild) = Non-Referable; Grade 2, 3, 4 = Referable DR
ref_threshold = CONFIG["referable_threshold"]
binary_true = (test_labels >= ref_threshold).astype(int)
binary_pred = (test_preds >= ref_threshold).astype(int)

bin_cm = confusion_matrix(binary_true, binary_pred, labels=[0, 1])
tn, fp, fn, tp = bin_cm.ravel()

sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0   # Sensitivity / Recall of referable cases
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0   # Specificity of non-referable cases
referable_acc = (tp + tn) / len(binary_true)
ppv = tp / (tp + fp) if (tp + fp) > 0 else 0.0           # Precision
npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
referable_f1 = (2 * tp) / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0.0

print("=" * 65)
print("CLINICAL REFERABLE DR METRICS (Grades 0-1 vs Grades 2-4)")
print("=" * 65)
print(f"True Positives  (Referable DR correctly flagged)       : {tp}")
print(f"False Negatives (Referable DR missed - Critical risk)   : {fn}")
print(f"True Negatives  (Non-referable correctly cleared)       : {tn}")
print(f"False Positives (Over-referral / False alarm)           : {fp}")
print("-" * 65)
print(f"Sensitivity (Recall of Referable DR)                    : {sensitivity * 100:.2f}%")
print(f"Specificity (True Negative Rate)                        : {specificity * 100:.2f}%")
print(f"Binary Referable DR Accuracy                            : {referable_acc * 100:.2f}%")
print(f"Positive Predictive Value (PPV / Precision)             : {ppv * 100:.2f}%")
print(f"Negative Predictive Value (NPV)                         : {npv * 100:.2f}%")
print(f"Binary Referable F1-Score                               : {referable_f1:.4f}")
print("=" * 65)

# Binary confusion matrix plot
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(
    bin_cm,
    annot=True,
    fmt="d",
    cmap="Greens",
    xticklabels=["Non-Referable (<2)", "Referable DR (>=2)"],
    yticklabels=["Non-Referable (<2)", "Referable DR (>=2)"],
    ax=ax
)
ax.set_title("Binary Referable DR Confusion Matrix", fontsize=12, fontweight="bold")
ax.set_xlabel("Predicted Clinical Status", fontsize=10)
ax.set_ylabel("True Clinical Status", fontsize=10)
plt.tight_layout()
bin_cm_path = PATHS["plots_dir"] / "referable_dr_confusion_matrix.png"
plt.savefig(bin_cm_path, dpi=200)
plt.show()

# Save complete evaluation report
test_metrics_summary = {
    "dataset": "APTOS 2019 Locked Test Set",
    "total_test_samples": int(len(test_labels)),
    "overall_accuracy": float(test_acc),
    "macro_precision": float(test_macro_prec),
    "macro_recall": float(test_macro_rec),
    "macro_f1": float(test_macro_f1),
    "weighted_f1": float(test_weighted_f1),
    "referable_dr": {
        "threshold_grade": ref_threshold,
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "accuracy": float(referable_acc),
        "precision_ppv": float(ppv),
        "npv": float(npv),
        "f1_score": float(referable_f1),
        "tp": int(tp),
        "fn": int(fn),
        "tn": int(tn),
        "fp": int(fp)
    },
    "per_class_report": cls_report
}

report_json_path = PATHS["reports_dir"] / "test_metrics_report.json"
with open(report_json_path, "w") as f:
    json.dump(test_metrics_summary, f, indent=4)
print(f"Saved complete metrics report to: {report_json_path}")""")

# -----------------------------------------------------------------------------
# SECTION 15
# -----------------------------------------------------------------------------
add_markdown("""## 15. Clinical Retinopathy Prediction Function
Provides `predict_retinopathy` for single images or PIL inputs with visualization of class probabilities and clinical referral advice.""")

add_code("""# =============================================================================
# 15. PREDICTION FUNCTION & VISUAL SHOWCASE
# =============================================================================
def predict_retinopathy(image_input, model, device, config=CONFIG):
    \"\"\"
    Inference helper: accepts file path or PIL Image and outputs grade,
    class probabilities, and clinical referral recommendation.
    \"\"\"
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input).convert("RGB")
    else:
        img = image_input.convert("RGB")

    if config["crop_borders"]:
        cropped = crop_fundus_borders(img)
    else:
        cropped = img

    tensor = eval_transforms(cropped).unsqueeze(0).to(device)

    model.eval()
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        pred_grade = int(np.argmax(probs))
        confidence = float(probs[pred_grade])

    is_referable = (pred_grade >= config["referable_threshold"])
    referral_text = (
        "REFERRAL REQUIRED (Grades 2-4)" if is_referable
        else "Non-Referable / Routine Annual Screening (Grades 0-1)"
    )

    return {
        "predicted_grade": pred_grade,
        "class_name": config["class_names"][pred_grade],
        "confidence": confidence,
        "is_referable": is_referable,
        "referral_recommendation": referral_text,
        "raw_probs": probs,
        "original_image": img,
        "cropped_image": cropped
    }

def visualize_prediction(image_path, model, device, true_grade=None):
    \"\"\"Plots fundus image side-by-side with horizontal probability bars.\"\"\"
    result = predict_retinopathy(image_path, model, device)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.imshow(result["original_image"])
    title_str = f"Predicted: {result['class_name']}\\nConfidence: {result['confidence'] * 100:.1f}%"
    if true_grade is not None:
        title_str += f"\\nTrue Grade: {CONFIG['class_names'][true_grade]}"
    ax1.set_title(title_str, fontsize=12, fontweight="bold")
    ax1.axis("off")

    grades = CONFIG["class_names_short"]
    probs = result["raw_probs"]
    colors = ["#e41a1c" if i == result["predicted_grade"] else "#3182bd" for i in range(5)]

    bars = ax2.barh(grades, probs, color=colors)
    ax2.set_xlim(0, 1.0)
    ax2.set_xlabel("Predicted Probability", fontsize=11)
    ax2.set_title(
        f"Clinical Action: {result['referral_recommendation']}",
        fontsize=11,
        fontweight="bold",
        color="red" if result["is_referable"] else "green"
    )
    ax2.grid(axis="x", linestyle="--", alpha=0.5)

    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 0.02, bar.get_y() + bar.get_height() / 2, f"{w * 100:.1f}%", va="center", fontsize=10)

    plt.tight_layout()
    plt.show()

print("Demonstrating prediction function on sample test images:")
sample_test_subset = df_test.sample(3, random_state=CONFIG["seed"])
for _, row in sample_test_subset.iterrows():
    sample_img_path = aptos_img_dir / f"{row['id_code']}.png"
    visualize_prediction(sample_img_path, model, device, true_grade=row["diagnosis"])""")

# -----------------------------------------------------------------------------
# SECTION 16
# -----------------------------------------------------------------------------
add_markdown("""## 16. IDRiD Label Format & Compatibility Verification
Verifies external IDRiD dataset directory, handles column name whitespace and trailing commas, validates 0–4 scale alignment, and checks for image files.""")

add_code("""# =============================================================================
# 16. IDRiD LABEL FORMAT & COMPATIBILITY VERIFICATION
# =============================================================================
print("=" * 75)
print("VERIFYING IDRiD EXTERNAL EVALUATION DATASET")
print("=" * 75)

idrid_test_csv_path = PATHS["idrid_test_csv"]
idrid_test_img_dir = PATHS["idrid_test_images"]

print(f"Checking IDRiD Groundtruth CSV at : {idrid_test_csv_path}")
print(f"Checking IDRiD Images Directory at: {idrid_test_img_dir}")

IDRID_COMPATIBLE = False

if not idrid_test_csv_path.exists():
    print(f"❌ IDRiD test groundtruth CSV not found at {idrid_test_csv_path}.")
    print("   Please extract IDRiD files to data/raw/idrid/disease_grading/.")
elif not idrid_test_img_dir.exists():
    print(f"❌ IDRiD test images directory not found at {idrid_test_img_dir}.")
else:
    # Inspect both IDRiD CSVs and verify columns
    print("Checking IDRiD Groundtruth CSV files...")
    train_gt_path = PATHS["idrid_train_csv"]
    if train_gt_path.exists():
        df_idrid_train_raw = pd.read_csv(train_gt_path)
        train_unnamed = [c for c in df_idrid_train_raw.columns if "unnamed" in c.lower()]
        print(f"   • Training CSV ({len(df_idrid_train_raw)} rows): {len(train_unnamed)} trailing 'Unnamed' artifact columns detected.")
        print("   • Confirming: IDRiD 413-image training set is NOT used for model training or tuning in this initial experiment.")

    df_idrid = pd.read_csv(idrid_test_csv_path)

    # Strip column name whitespace and verify Unnamed artifact columns
    df_idrid.columns = [str(c).strip() for c in df_idrid.columns]
    unnamed_cols = [c for c in df_idrid.columns if "unnamed" in c.lower()]
    for c in unnamed_cols:
        non_null = df_idrid[c].dropna()
        is_empty = all(str(v).strip() == "" for v in non_null)
        print(f"   • Column '{c}' confirmed empty artifact: {is_empty} ({len(non_null)} non-null entries)")

    if unnamed_cols:
        df_idrid = df_idrid.drop(columns=unnamed_cols)
        print(f"   • Excluded {len(unnamed_cols)} empty 'Unnamed' artifact columns from IDRiD test CSV.")

    print(f"\nCleaned IDRiD Testing CSV Columns: {df_idrid.columns.tolist()}")

    # Find image and grading columns
    img_col_candidates = [c for c in df_idrid.columns if "image" in c.lower() or "id" in c.lower()]
    grade_col_candidates = [c for c in df_idrid.columns if "retinopathy" in c.lower() or "grade" in c.lower()]

    if not img_col_candidates or not grade_col_candidates:
        print("❌ Could not locate image and grade columns in IDRiD CSV.")
        print(f"   Available columns: {df_idrid.columns.tolist()}")
    else:
        idrid_img_col = img_col_candidates[0]
        idrid_grade_col = grade_col_candidates[0]
        print(f"✅ Identified Image Column: '{idrid_img_col}', Grade Column: '{idrid_grade_col}'")
        if "Risk of macular edema" in df_idrid.columns:
            print("ℹ️ Note: Ignoring 'Risk of macular edema' column for 5-class DR task.")

        # Clean NaN rows and cast grades
        df_idrid = df_idrid.dropna(subset=[idrid_img_col, idrid_grade_col])
        df_idrid[idrid_grade_col] = df_idrid[idrid_grade_col].astype(int)

        unique_grades = sorted(df_idrid[idrid_grade_col].unique())
        print(f"IDRiD Unique Grades found: {unique_grades}")

        is_scale_compatible = set(unique_grades).issubset({0, 1, 2, 3, 4})
        print(f"Grading scale compatible with APTOS (0-4): {is_scale_compatible}")

        # Verify image existence on disk
        print("\\nVerifying presence of IDRiD image files on disk...")
        found_images = 0
        missing_images = []

        for img_id in df_idrid[idrid_img_col]:
            name_str = str(img_id)
            candidates = [
                idrid_test_img_dir / name_str,
                idrid_test_img_dir / f"{name_str}.jpg",
                idrid_test_img_dir / f"{name_str}.JPG",
                idrid_test_img_dir / f"{name_str}.png"
            ]
            if any(p.exists() for p in candidates):
                found_images += 1
            else:
                missing_images.append(name_str)

        print(f"Images verified on disk: {found_images} / {len(df_idrid)} ({found_images / len(df_idrid) * 100:.1f}%)")

        if missing_images:
            print(f"⚠️ {len(missing_images)} image files missing (e.g. {missing_images[:3]}).")

        if is_scale_compatible and found_images > 0:
            IDRID_COMPATIBLE = True
            print("\\n✅ IDRiD EXTERNAL DATASET IS COMPATIBLE! Ready for zero-shot evaluation.")

            id_dist = df_idrid[idrid_grade_col].value_counts().sort_index()
            id_dist_df = pd.DataFrame({
                "Grade": id_dist.index,
                "Diagnosis": [CONFIG["class_names"][i] for i in id_dist.index],
                "Count": id_dist.values,
                "Percentage": [f"{c / len(df_idrid) * 100:.2f}%" for c in id_dist.values]
            })
            display(id_dist_df)
        else:
            print("❌ IDRiD compatibility checks failed.")

print("=" * 75)""")

# -----------------------------------------------------------------------------
# SECTION 17
# -----------------------------------------------------------------------------
add_markdown("""## 17. IDRiD Zero-Shot External Evaluation & Domain Shift Analysis
Tests out-of-domain generalization on IDRiD without fine-tuning, plots the external confusion matrix, and compares in-domain vs out-of-domain performance.""")

add_code("""# =============================================================================
# 17. IDRiD ZERO-SHOT EXTERNAL EVALUATION & DOMAIN SHIFT ANALYSIS
# =============================================================================
if not IDRID_COMPATIBLE:
    print("⚠️ IDRiD dataset not available or failed compatibility verification.")
    print("   Skipping external evaluation. Re-run after placing IDRiD files in data/raw/idrid/.")
else:
    print("Running Zero-Shot External Evaluation on IDRiD with APTOS-Trained EfficientNet-B0...")

    idrid_dataset = RetinopathyDataset(
        df_idrid,
        idrid_test_img_dir,
        transform=eval_transforms,
        crop_borders=CONFIG["crop_borders"],
        img_col=idrid_img_col,
        label_col=idrid_grade_col,
        img_ext=".jpg"
    )

    idrid_loader = DataLoader(
        idrid_dataset,
        batch_size=CONFIG["batch_size"],
        shuffle=False,
        num_workers=CONFIG["num_workers"]
    )

    idrid_preds = []
    idrid_labels = []

    model.eval()
    with torch.no_grad():
        for images, labels, _ in idrid_loader:
            images = images.to(device)
            outputs = model(images)
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            idrid_preds.extend(preds)
            idrid_labels.extend(labels.numpy())

    idrid_preds = np.array(idrid_preds)
    idrid_labels = np.array(idrid_labels)

    # Metrics on IDRiD
    id_acc = accuracy_score(idrid_labels, idrid_preds)
    id_macro_f1 = f1_score(idrid_labels, idrid_preds, average="macro", zero_division=0)
    id_weighted_f1 = f1_score(idrid_labels, idrid_preds, average="weighted", zero_division=0)

    # Referable DR on IDRiD
    id_bin_true = (idrid_labels >= ref_threshold).astype(int)
    id_bin_pred = (idrid_preds >= ref_threshold).astype(int)
    id_bin_cm = confusion_matrix(id_bin_true, id_bin_pred, labels=[0, 1])
    id_tn, id_fp, id_fn, id_tp = id_bin_cm.ravel()

    id_sens = id_tp / (id_tp + id_fn) if (id_tp + id_fn) > 0 else 0.0
    id_spec = id_tn / (id_tn + id_fp) if (id_tn + id_fp) > 0 else 0.0
    id_ref_acc = (id_tp + id_tn) / len(id_bin_true)

    print("=" * 75)
    print("IDRiD ZERO-SHOT EXTERNAL GENERALIZATION RESULTS")
    print("=" * 75)
    print(f"Total IDRiD Test Samples Evaluated : {len(idrid_labels)}")
    print(f"Overall Accuracy                   : {id_acc * 100:.2f}%")
    print(f"Macro F1 Score                     : {id_macro_f1:.4f}")
    print(f"Weighted F1 Score                  : {id_weighted_f1:.4f}")
    print("-" * 75)
    print(f"Referable DR Sensitivity           : {id_sens * 100:.2f}%")
    print(f"Referable DR Specificity           : {id_spec * 100:.2f}%")
    print(f"Binary Referable DR Accuracy       : {id_ref_acc * 100:.2f}%")
    print("=" * 75)

    # IDRiD Confusion Matrix
    id_cm = confusion_matrix(idrid_labels, idrid_preds, labels=range(5))

    plt.figure(figsize=(8, 6.5))
    sns.heatmap(
        id_cm,
        annot=True,
        fmt="d",
        cmap="Oranges",
        xticklabels=CONFIG["class_names_short"],
        yticklabels=CONFIG["class_names_short"]
    )
    plt.title("IDRiD External Test Confusion Matrix (Zero-Shot Generalization)", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted DR Grade (APTOS Model)", fontsize=11)
    plt.ylabel("True IDRiD Ground Truth Grade", fontsize=11)
    plt.tight_layout()
    id_cm_path = PATHS["plots_dir"] / "idrid_confusion_matrix.png"
    plt.savefig(id_cm_path, dpi=200)
    plt.show()
    print(f"Saved IDRiD confusion matrix to: {id_cm_path}")

    # Side-by-side comparison table: In-Domain (APTOS) vs Out-of-Domain (IDRiD)
    comparison_df = pd.DataFrame({
        "Performance Metric": [
            "Evaluated Samples",
            "Overall Accuracy",
            "Macro F1 Score",
            "Weighted F1 Score",
            "Referable DR Sensitivity",
            "Referable DR Specificity",
            "Referable DR Accuracy"
        ],
        "In-Domain (APTOS Test Split)": [
            len(test_labels),
            f"{test_acc * 100:.2f}%",
            f"{test_macro_f1:.4f}",
            f"{test_weighted_f1:.4f}",
            f"{sensitivity * 100:.2f}%",
            f"{specificity * 100:.2f}%",
            f"{referable_acc * 100:.2f}%"
        ],
        "Out-of-Domain (IDRiD External)": [
            len(idrid_labels),
            f"{id_acc * 100:.2f}%",
            f"{id_macro_f1:.4f}",
            f"{id_weighted_f1:.4f}",
            f"{id_sens * 100:.2f}%",
            f"{id_spec * 100:.2f}%",
            f"{id_ref_acc * 100:.2f}%"
        ]
    })
    print("\\nIN-DOMAIN VS OUT-OF-DOMAIN GENERALIZATION COMPARISON:")
    display(comparison_df)

    # Save IDRiD metrics report
    idrid_report = {
        "dataset": "IDRiD Disease Grading Testing Set",
        "total_samples": int(len(idrid_labels)),
        "overall_accuracy": float(id_acc),
        "macro_f1": float(id_macro_f1),
        "weighted_f1": float(id_weighted_f1),
        "referable_dr": {
            "sensitivity": float(id_sens),
            "specificity": float(id_spec),
            "accuracy": float(id_ref_acc),
            "tp": int(id_tp),
            "fn": int(id_fn),
            "tn": int(id_tn),
            "fp": int(id_fp)
        },
        "per_class_report": classification_report(
            idrid_labels,
            idrid_preds,
            target_names=CONFIG["class_names"],
            output_dict=True,
            zero_division=0
        )
    }
    idrid_report_path = PATHS["reports_dir"] / "idrid_metrics_report.json"
    with open(idrid_report_path, "w") as f:
        json.dump(idrid_report, f, indent=4)
    print(f"Saved IDRiD metrics report to: {idrid_report_path}")""")

# -----------------------------------------------------------------------------
# SECTION 18
# -----------------------------------------------------------------------------
add_markdown("""## 18. Saved Artifacts Audit & Google Drive Verification
Audits all generated checkpoints, split manifests, plots, and metric reports to verify they are securely saved to Google Drive.""")

add_code("""# =============================================================================
# 18. SAVED ARTIFACTS AUDIT & GOOGLE DRIVE VERIFICATION
# =============================================================================
print("=" * 75)
print("SAVED PROJECT ARTIFACTS AUDIT")
print("=" * 75)

for label, path_key in [
    ("Model Checkpoints", "checkpoints_dir"),
    ("Data Splits Manifests", "splits_dir"),
    ("Evaluation Plots", "plots_dir"),
    ("Metric Reports", "reports_dir")
]:
    d = PATHS[path_key]
    print(f"\\n📁 {label} ({d}):")
    if d.exists():
        items = list(d.iterdir())
        if not items:
            print("   (empty)")
        for item in sorted(items):
            mb = item.stat().st_size / (1024 * 1024)
            print(f"   • {item.name:38s} [{mb:6.2f} MB]")
    else:
        print("   (does not exist)")

print("\\n" + "=" * 75)
print("🎉 ALL WORKFLOW STEPS COMPLETE!")
print("=" * 75)""")

# Construct Notebook JSON structure
notebook_data = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {
            "provenance": [],
            "toc_visible": True
        },
        "kernelspec": {
            "display_name": "Python 3",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.12"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 0
}

# Write notebook to project root
target_file_root = ROOT / "DR_Classification_Training.ipynb"
with open(target_file_root, "w", encoding="utf-8") as f:
    json.dump(notebook_data, f, indent=2, ensure_ascii=False)
print(f"Successfully created notebook at root: {target_file_root}")

# Also write notebook to notebooks/ directory for convenience
target_file_nb = ROOT / "notebooks" / "DR_Classification_Training.ipynb"
with open(target_file_nb, "w", encoding="utf-8") as f:
    json.dump(notebook_data, f, indent=2, ensure_ascii=False)
print(f"Successfully created notebook in notebooks/: {target_file_nb}")
print(f"Total cells generated: {len(cells)}")
