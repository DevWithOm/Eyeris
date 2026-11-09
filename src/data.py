"""
Diabetic Retinopathy Dataset Preparation, Integrity Checks, and DataLoaders.
Supports APTOS 2019 (primary) and IDRiD (external validation).
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

# Standard ImageNet normalization parameters
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def crop_fundus_borders(image: Image.Image, tol: int = 10) -> Image.Image:
    """
    Detects and crops black outer margins from retinal fundus photographs.
    Focuses convolutional neural network receptive fields on diagnostic retinal tissue.
    """
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

    # Prevent degenerate crops
    if (ymax - ymin < 50) or (xmax - xmin < 50):
        return image

    return image.crop((xmin, ymin, xmax, ymax))


def get_transforms(image_size: int = 224, is_training: bool = True) -> transforms.Compose:
    """
    Returns image transformation pipelines.
    Training uses clinically sensible augmentations (flips, slight rotations, color jitter).
    Validation/Testing strictly uses deterministic resizing and ImageNet normalization.
    """
    normalize = transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)

    if is_training:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(degrees=20),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            normalize,
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            normalize,
        ])


def validate_aptos_dataset(csv_path: Union[str, Path], img_dir: Union[str, Path]) -> Tuple[pd.DataFrame, Dict]:
    """
    Inspects and validates APTOS train.csv and training images directory.
    Checks:
      - File and directory existence
      - Required columns ('id_code', 'diagnosis')
      - Missing / NaN values
      - Duplicate image IDs
      - Valid class label range (0 to 4)
      - Existence of corresponding .png image on disk for every CSV record
    """
    csv_path = Path(csv_path)
    img_dir = Path(img_dir)

    if not csv_path.exists():
        raise FileNotFoundError(f"APTOS CSV not found at: {csv_path}")
    if not img_dir.exists():
        raise FileNotFoundError(f"APTOS image directory not found at: {img_dir}")

    df = pd.read_csv(csv_path)
    initial_rows = len(df)

    # Check required columns
    required_cols = ["id_code", "diagnosis"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in APTOS CSV {csv_path}")

    # Check missing values
    missing_ids = int(df["id_code"].isnull().sum())
    missing_labels = int(df["diagnosis"].isnull().sum())

    # Check duplicates
    duplicate_ids = int(df["id_code"].duplicated().sum())

    # Drop nulls if any exist
    if missing_ids > 0 or missing_labels > 0:
        df = df.dropna(subset=required_cols).reset_index(drop=True)

    # Verify class labels
    df["diagnosis"] = df["diagnosis"].astype(int)
    unique_classes = sorted(df["diagnosis"].unique().tolist())
    invalid_classes = [c for c in unique_classes if c not in {0, 1, 2, 3, 4}]
    if invalid_classes:
        raise ValueError(f"Detected invalid class labels in APTOS CSV: {invalid_classes}. Expected only 0..4.")

    # Match images on disk
    img_files = {f.name: f for f in img_dir.iterdir() if f.is_file()}
    file_stems = {f.stem: f.name for f in img_dir.iterdir() if f.is_file()}

    missing_images = []
    for img_id in df["id_code"]:
        id_str = str(img_id).strip()
        if id_str not in file_stems and f"{id_str}.png" not in img_files:
            missing_images.append(id_str)

    report = {
        "dataset": "APTOS 2019",
        "csv_path": str(csv_path),
        "img_dir": str(img_dir),
        "total_rows_initial": initial_rows,
        "valid_rows": len(df),
        "missing_ids": missing_ids,
        "missing_labels": missing_labels,
        "duplicate_ids": duplicate_ids,
        "unique_classes": unique_classes,
        "class_distribution": df["diagnosis"].value_counts().sort_index().to_dict(),
        "total_images_in_dir": len(img_files),
        "missing_images_on_disk": len(missing_images),
        "sample_missing_images": missing_images[:5],
        "is_valid": (len(missing_images) == 0 and duplicate_ids == 0 and len(invalid_classes) == 0)
    }

    if missing_images:
        raise FileNotFoundError(f"{len(missing_images)} APTOS images referenced in CSV are missing on disk.")

    return df, report


def validate_idrid_dataset(
    csv_path: Union[str, Path],
    img_dir: Union[str, Path],
    is_test_set: bool = False
) -> Tuple[pd.DataFrame, Dict]:
    """
    Inspects IDRiD groundtruth CSV and images directory.
    Identifies exact columns for image IDs and DR grading labels.
    Confirms and drops empty 'Unnamed' artifact columns.
    Ignores 'Risk of macular edema'.
    Verifies image presence on disk (.jpg).
    """
    csv_path = Path(csv_path)
    img_dir = Path(img_dir)

    if not csv_path.exists():
        raise FileNotFoundError(f"IDRiD CSV not found at: {csv_path}")
    if not img_dir.exists():
        raise FileNotFoundError(f"IDRiD image directory not found at: {img_dir}")

    df = pd.read_csv(csv_path)
    initial_rows = len(df)
    initial_cols = list(df.columns)

    # Clean whitespace in column names
    df.columns = [str(c).strip() for c in df.columns]

    # Inspect Unnamed columns
    unnamed_cols = [c for c in df.columns if "unnamed" in c.lower()]
    unnamed_inspection = {}
    for c in unnamed_cols:
        non_null_vals = df[c].dropna().tolist()
        # Check if non-null values are purely whitespace
        is_effectively_empty = all(str(v).strip() == "" for v in non_null_vals)
        unnamed_inspection[c] = {
            "non_null_count": len(non_null_vals),
            "is_effectively_empty": is_effectively_empty
        }

    # Safely exclude Unnamed columns
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    # Locate Image ID column and DR grading column
    img_candidates = [c for c in df.columns if "image" in c.lower() or "id" in c.lower()]
    dr_candidates = [c for c in df.columns if "retinopathy" in c.lower() or "grade" in c.lower()]

    if not img_candidates:
        raise KeyError(f"Could not identify Image ID column in IDRiD CSV. Available: {df.columns.tolist()}")
    if not dr_candidates:
        raise KeyError(f"Could not identify DR grading column in IDRiD CSV. Available: {df.columns.tolist()}")

    id_col = img_candidates[0]
    grade_col = dr_candidates[0]

    # Drop null rows if any
    df = df.dropna(subset=[id_col, grade_col]).reset_index(drop=True)
    duplicate_ids = int(df[id_col].duplicated().sum())

    # Cast grade to int and check unique classes
    df[grade_col] = df[grade_col].astype(int)
    unique_classes = sorted(df[grade_col].unique().tolist())
    invalid_classes = [c for c in unique_classes if c not in {0, 1, 2, 3, 4}]
    if invalid_classes:
        raise ValueError(f"Invalid DR grade classes in IDRiD CSV: {invalid_classes}")

    # Verify images on disk
    img_files = {f.name: f for f in img_dir.iterdir() if f.is_file()}
    file_stems = {f.stem: f.name for f in img_dir.iterdir() if f.is_file()}

    missing_images = []
    for img_id in df[id_col]:
        id_str = str(img_id).strip()
        candidates = [id_str, f"{id_str}.jpg", f"{id_str}.JPG", f"{id_str}.png"]
        if not any(c in img_files or id_str in file_stems for c in candidates):
            missing_images.append(id_str)

    report = {
        "dataset": "IDRiD " + ("Testing Set" if is_test_set else "Training Set"),
        "csv_path": str(csv_path),
        "img_dir": str(img_dir),
        "initial_rows": initial_rows,
        "initial_columns": initial_cols,
        "identified_id_col": id_col,
        "identified_grade_col": grade_col,
        "unnamed_cols_excluded": unnamed_cols,
        "unnamed_cols_status": unnamed_inspection,
        "ignored_columns": [c for c in df.columns if c not in [id_col, grade_col]],
        "valid_rows": len(df),
        "duplicate_ids": duplicate_ids,
        "unique_classes": unique_classes,
        "class_distribution": df[grade_col].value_counts().sort_index().to_dict(),
        "total_images_in_dir": len(img_files),
        "missing_images_on_disk": len(missing_images),
        "sample_missing_images": missing_images[:5],
        "is_valid": (len(missing_images) == 0 and duplicate_ids == 0 and len(invalid_classes) == 0)
    }

    if missing_images:
        raise FileNotFoundError(f"{len(missing_images)} IDRiD images referenced in CSV are missing on disk.")

    return df, report


def create_stratified_splits(
    df: pd.DataFrame,
    target_ratios: Tuple[float, float, float] = (0.70, 0.15, 0.15),
    seed: int = 42,
    label_col: str = "diagnosis",
    id_col: str = "id_code",
    output_dir: Optional[Union[str, Path]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Creates reproducible stratified train/validation/test splits with target ratio (70/15/15).
    Verifies that no duplicate images or overlapping identifiers exist between splits.
    Saves locked split manifests to output_dir without altering the original dataset.
    """
    train_ratio, val_ratio, test_ratio = target_ratios
    total_ratio = train_ratio + val_ratio + test_ratio
    assert np.isclose(total_ratio, 1.0), f"Ratios must sum to 1.0, got {total_ratio}"

    # Step 1: Split into Train (70%) and Temp (30%)
    temp_ratio = val_ratio + test_ratio
    df_train, df_temp = train_test_split(
        df,
        test_size=temp_ratio,
        stratify=df[label_col],
        random_state=seed
    )

    # Step 2: Split Temp into Validation (15%) and Test (15%)
    val_relative_ratio = val_ratio / temp_ratio
    df_val, df_test = train_test_split(
        df_temp,
        test_size=(1.0 - val_relative_ratio),
        stratify=df_temp[label_col],
        random_state=seed
    )

    # Reset indices
    df_train = df_train.reset_index(drop=True)
    df_val = df_val.reset_index(drop=True)
    df_test = df_test.reset_index(drop=True)

    # Verification: Zero identifier overlap
    train_ids = set(df_train[id_col])
    val_ids = set(df_val[id_col])
    test_ids = set(df_test[id_col])

    overlap_train_val = train_ids & val_ids
    overlap_train_test = train_ids & test_ids
    overlap_val_test = val_ids & test_ids

    if overlap_train_val or overlap_train_test or overlap_val_test:
        raise ValueError(
            f"Overlapping identifiers detected across splits!\n"
            f"Train & Val: {len(overlap_train_val)}, "
            f"Train & Test: {len(overlap_train_test)}, "
            f"Val & Test: {len(overlap_val_test)}"
        )

    # Verification: All classes represented in every split
    for split_name, split_df in [("Train", df_train), ("Val", df_val), ("Test", df_test)]:
        unique_classes = set(split_df[label_col].unique())
        if unique_classes != {0, 1, 2, 3, 4}:
            raise ValueError(f"Incomplete class coverage in {split_name} split: {unique_classes}")

    # Save split manifests if output_dir provided
    if output_dir is not None:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        df_train.to_csv(out_path / "train_split.csv", index=False)
        df_val.to_csv(out_path / "val_split.csv", index=False)
        df_test.to_csv(out_path / "test_split.csv", index=False)

    return df_train, df_val, df_test


class RetinopathyDataset(Dataset):
    """
    Custom PyTorch Dataset for Retinal Fundus Photographs.
    Supports border auto-cropping, data augmentations, and multiple image formats (.png, .jpg).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        img_dir: Union[str, Path],
        transform: Optional[transforms.Compose] = None,
        crop_borders: bool = True,
        img_col: str = "id_code",
        label_col: str = "diagnosis",
        default_ext: str = ".png"
    ):
        self.df = df.reset_index(drop=True)
        self.img_dir = Path(img_dir)
        self.transform = transform
        self.crop_borders = crop_borders
        self.img_col = img_col
        self.label_col = label_col
        self.default_ext = default_ext

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, str]:
        row = self.df.iloc[idx]
        img_name = str(row[self.img_col]).strip()

        # Locate image file
        img_path = self.img_dir / img_name
        if not img_path.exists():
            for ext in [self.default_ext, ".png", ".jpg", ".JPG", ".jpeg"]:
                candidate = self.img_dir / f"{img_name}{ext}"
                if candidate.exists():
                    img_path = candidate
                    break

        if not img_path.exists():
            raise FileNotFoundError(f"Image not found on disk: {img_name} in {self.img_dir}")

        image = Image.open(img_path).convert("RGB")

        if self.crop_borders:
            image = crop_fundus_borders(image)

        if self.transform is not None:
            image = self.transform(image)

        label = int(row[self.label_col])
        return image, torch.tensor(label, dtype=torch.long), img_name


def compute_class_weights(
    df: pd.DataFrame,
    label_col: str = "diagnosis",
    num_classes: int = 5,
    method: str = "balanced"
) -> torch.Tensor:
    """
    Computes class weights to handle severe class imbalance in the training set.
    Method 'balanced': weight_c = total_samples / (num_classes * count_c).
    """
    counts = df[label_col].value_counts().sort_index()
    total_samples = len(df)
    weights = np.zeros(num_classes, dtype=np.float32)

    for c in range(num_classes):
        count = counts.get(c, 0)
        if count > 0:
            if method == "balanced":
                weights[c] = total_samples / (num_classes * count)
            elif method == "inverse":
                weights[c] = 1.0 / count
        else:
            weights[c] = 1.0

    # Normalize weights so mean is 1.0
    weights = weights / weights.mean()
    return torch.tensor(weights, dtype=torch.float32)


def get_dataloaders(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    img_dir: Union[str, Path],
    batch_size: int = 16,
    num_workers: int = 0,
    image_size: int = 224,
    crop_borders: bool = True
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Builds PyTorch DataLoaders for train, validation, and test splits.
    """
    train_transforms = get_transforms(image_size=image_size, is_training=True)
    eval_transforms = get_transforms(image_size=image_size, is_training=False)

    train_dataset = RetinopathyDataset(
        train_df, img_dir, transform=train_transforms, crop_borders=crop_borders
    )
    val_dataset = RetinopathyDataset(
        val_df, img_dir, transform=eval_transforms, crop_borders=crop_borders
    )
    test_dataset = RetinopathyDataset(
        test_df, img_dir, transform=eval_transforms, crop_borders=crop_borders
    )

    pin_memory = torch.cuda.is_available()

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory
    )

    return train_loader, val_loader, test_loader
