"""IDRiD Retinal Lesion Segmentation Dataset and DataLoader Module.

Provides:
- IDRiDDataset: PyTorch Dataset for paired retinal fundus images and lesion masks.
- SynchronizedTransform: Synchronized spatial & color transformations for image-mask pairs.
- split_idrid_dataset: Image-level reproducible dataset splitting preventing data leakage.
- create_segmentation_dataloaders: PyTorch DataLoader factory for train, val, and test splits.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Supported lesion classes and their groundtruth directory/file patterns
LESION_CLASSES: Tuple[str, ...] = ("MA", "HE", "EX", "SE")

LESION_FOLDER_MAP: Dict[str, str] = {
    "MA": "1. Microaneurysms",
    "HE": "2. Haemorrhages",
    "EX": "3. Hard Exudates",
    "SE": "4. Soft Exudates",
    "OD": "5. Optic Disc",
}

LESION_SUFFIX_MAP: Dict[str, str] = {
    "MA": "_MA.tif",
    "HE": "_HE.tif",
    "EX": "_EX.tif",
    "SE": "_SE.tif",
    "OD": "_OD.tif",
}

DEFAULT_IMAGENET_MEAN = (0.485, 0.456, 0.406)
DEFAULT_IMAGENET_STD = (0.229, 0.224, 0.225)


class SynchronizedTransform:
    """Applies synchronized spatial transformations to images and masks.

    Ensures that masks are strictly interpolated with NEAREST-NEIGHBOR
    interpolation to preserve binary/categorical ground-truth values without
    interpolation artifacts.
    """

    def __init__(
        self,
        img_size: Tuple[int, int] = (512, 512),
        is_train: bool = True,
        hflip_prob: float = 0.5,
        vflip_prob: float = 0.5,
        rot90_prob: float = 0.5,
        mean: Sequence[float] = DEFAULT_IMAGENET_MEAN,
        std: Sequence[float] = DEFAULT_IMAGENET_STD,
    ) -> None:
        self.img_size = img_size  # (height, width)
        self.is_train = is_train
        self.hflip_prob = hflip_prob
        self.vflip_prob = vflip_prob
        self.rot90_prob = rot90_prob
        self.mean = torch.tensor(mean, dtype=torch.float32).view(3, 1, 1)
        self.std = torch.tensor(std, dtype=torch.float32).view(3, 1, 1)

    def __call__(
        self,
        image: Image.Image,
        masks: List[Optional[Image.Image]],
        mask_valid: List[bool],
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Apply synchronized transformations.

        Args:
            image: PIL RGB image of shape (W, H).
            masks: List of PIL Image masks (or None if missing), each of shape (W, H).
            mask_valid: Boolean list indicating if each mask in `masks` was present.

        Returns:
            image_tensor: FloatTensor of shape (3, H, W), normalized.
            masks_tensor: FloatTensor of shape (C, H, W) with values in {0.0, 1.0}.
        """
        target_w, target_h = self.img_size[1], self.img_size[0]

        # 1. Resize image with BILINEAR
        resized_img = image.resize((target_w, target_h), resample=Image.Resampling.BILINEAR)

        # 2. Resize masks with NEAREST-NEIGHBOR interpolation
        resized_masks: List[Optional[Image.Image]] = []
        for m, valid in zip(masks, mask_valid):
            if valid and m is not None:
                resized_masks.append(
                    m.resize((target_w, target_h), resample=Image.Resampling.NEAREST)
                )
            else:
                resized_masks.append(None)

        # 3. Synchronized data augmentation for training
        if self.is_train:
            # Horizontal Flip
            if random.random() < self.hflip_prob:
                resized_img = resized_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                resized_masks = [
                    m.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if m is not None else None
                    for m in resized_masks
                ]

            # Vertical Flip
            if random.random() < self.vflip_prob:
                resized_img = resized_img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                resized_masks = [
                    m.transpose(Image.Transpose.FLIP_TOP_BOTTOM) if m is not None else None
                    for m in resized_masks
                ]

            # 90-degree rotations (orthogonal, preserving pixel alignment on circular retina)
            if random.random() < self.rot90_prob:
                rot_k = random.choice([1, 2, 3])
                rot_methods = {
                    1: Image.Transpose.ROTATE_90,
                    2: Image.Transpose.ROTATE_180,
                    3: Image.Transpose.ROTATE_270,
                }
                method = rot_methods[rot_k]
                resized_img = resized_img.transpose(method)
                resized_masks = [
                    m.transpose(method) if m is not None else None
                    for m in resized_masks
                ]

        # 4. Convert image to normalized FloatTensor
        img_np = np.array(resized_img, dtype=np.float32) / 255.0  # (H, W, 3)
        img_tensor = torch.from_numpy(img_np.transpose((2, 0, 1)))  # (3, H, W)
        img_tensor = (img_tensor - self.mean) / self.std

        # 5. Convert masks to FloatTensor of shape (C, H, W)
        num_classes = len(masks)
        mask_arrays = np.zeros((num_classes, target_h, target_w), dtype=np.float32)
        for c_idx, (m, valid) in enumerate(zip(resized_masks, mask_valid)):
            if valid and m is not None:
                arr = np.array(m)
                # Binarize: any positive value (>0) is foreground 1.0
                mask_arrays[c_idx] = (arr > 0).astype(np.float32)
            else:
                # Missing annotation: filled with zeros, tracked by mask_valid flag
                mask_arrays[c_idx] = 0.0

        masks_tensor = torch.from_numpy(mask_arrays)  # (C, H, W)

        return img_tensor, masks_tensor


class IDRiDDataset(Dataset):
    """PyTorch Dataset for IDRiD Retinal Fundus Images and Lesion Segmentation Masks.

    Guarantees:
    - Strict image-mask correspondence based on actual IDRiD naming conventions.
    - Explicit tracking of missing masks: missing annotations are flagged via
      `mask_valid` so loss functions and evaluators do not falsely assume they are negative.
    - Supports lesion classes: MA (Microaneurysms), HE (Haemorrhages), EX (Hard Exudates),
      SE (Soft Exudates).
    - Synchronized nearest-neighbor interpolation for ground-truth masks.
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        split: str = "train",
        image_ids: Optional[Sequence[str]] = None,
        classes: Sequence[str] = LESION_CLASSES,
        img_size: Tuple[int, int] = (512, 512),
        is_train: bool = True,
        transform: Optional[Callable] = None,
    ) -> None:
        """Initialize the IDRiD Dataset.

        Args:
            root_dir: Path to 'A. Segmentation' root or IDRiD base folder.
            split: 'train', 'test', or 'custom' (when image_ids is specified).
            image_ids: Optional explicit list of image IDs (e.g. ['IDRiD_01', 'IDRiD_02']).
            classes: Sequence of lesion class codes. Defaults to ('MA', 'HE', 'EX', 'SE').
            img_size: Output spatial resolution as (height, width).
            is_train: Whether data augmentation should be applied.
            transform: Optional custom synchronized transform callable.
        """
        self.root_dir = Path(root_dir)
        self.split = split.lower()
        self.classes = tuple(classes)
        self.img_size = img_size
        self.is_train = is_train

        # Validate classes
        for c in self.classes:
            if c not in LESION_FOLDER_MAP:
                raise ValueError(
                    f"Unsupported lesion class '{c}'. Supported classes are: {list(LESION_FOLDER_MAP.keys())}"
                )

        # Resolve dataset base directory
        self._resolve_directories()

        # Build list of paired samples
        self.samples: List[Dict[str, Union[str, Dict[str, Optional[str]]]]] = []
        self._build_index(image_ids)

        if len(self.samples) == 0:
            raise FileNotFoundError(
                f"No valid retinal images found in {self.images_dir}. "
                "Ensure IDRiD 'A. Segmentation' dataset is downloaded and extracted."
            )

        # Default transform if not provided
        self.transform = transform or SynchronizedTransform(
            img_size=self.img_size,
            is_train=self.is_train,
        )

    def _resolve_directories(self) -> None:
        """Locates images and groundtruth directories."""
        # Handle cases where root_dir is 'data/raw/IDRiD' vs 'data/raw/IDRiD/A. Segmentation'
        if (self.root_dir / "A. Segmentation").exists():
            seg_root = self.root_dir / "A. Segmentation"
        elif (self.root_dir / "1. Original Images").exists():
            seg_root = self.root_dir
        else:
            raise FileNotFoundError(
                f"Cannot locate IDRiD Segmentation directory at {self.root_dir}. "
                "Expected either 'A. Segmentation' subfolder or '1. Original Images'."
            )

        split_subfolder = "b. Testing Set" if self.split == "test" else "a. Training Set"
        self.images_dir = seg_root / "1. Original Images" / split_subfolder
        self.masks_base_dir = seg_root / "2. All Segmentation Groundtruths" / split_subfolder

        if not self.images_dir.exists():
            raise FileNotFoundError(
                f"Original images folder not found at: {self.images_dir}"
            )
        if not self.masks_base_dir.exists():
            raise FileNotFoundError(
                f"Groundtruths folder not found at: {self.masks_base_dir}"
            )

    def _build_index(self, explicit_image_ids: Optional[Sequence[str]] = None) -> None:
        """Indexes all images and matches them to corresponding lesion masks."""
        available_files = sorted(
            [f for f in os.listdir(self.images_dir) if f.lower().endswith((".jpg", ".jpeg"))]
        )

        explicit_set = set(explicit_image_ids) if explicit_image_ids is not None else None

        for fname in available_files:
            img_id = os.path.splitext(fname)[0]

            if explicit_set is not None and img_id not in explicit_set:
                continue

            img_path = str(self.images_dir / fname)
            mask_paths: Dict[str, Optional[str]] = {}

            for c in self.classes:
                folder_name = LESION_FOLDER_MAP[c]
                suffix = LESION_SUFFIX_MAP[c]
                candidate_name = f"{img_id}{suffix}"
                candidate_path = self.masks_base_dir / folder_name / candidate_name

                if candidate_path.exists():
                    mask_paths[c] = str(candidate_path)
                else:
                    # Ground truth mask absent
                    mask_paths[c] = None

            self.samples.append({
                "image_id": img_id,
                "image_path": img_path,
                "mask_paths": mask_paths,
            })

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, Union[torch.Tensor, str, Dict[str, bool]]]:
        """Loads and returns a paired (image, masks, mask_valid) sample.

        Returns:
            dict containing:
                'image': FloatTensor (3, H, W) normalized.
                'masks': FloatTensor (C, H, W) with values in {0.0, 1.0}.
                'mask_valid': BoolTensor (C,) indicating whether ground truth was present.
                'image_id': str identifier (e.g. 'IDRiD_01').
                'class_names': tuple of class names.
        """
        sample_info = self.samples[idx]
        img_id = str(sample_info["image_id"])
        img_path = str(sample_info["image_path"])
        mask_paths = sample_info["mask_paths"]  # type: ignore

        # Load RGB image
        try:
            with Image.open(img_path) as im:
                image = im.convert("RGB")
        except Exception as e:
            raise IOError(f"Failed to read image at {img_path}: {e}") from e

        # Load mask files
        raw_masks: List[Optional[Image.Image]] = []
        mask_valid: List[bool] = []

        for c in self.classes:
            m_path = mask_paths[c]
            if m_path is not None and os.path.exists(m_path):
                try:
                    with Image.open(m_path) as m_im:
                        # Open and ensure single-channel
                        raw_masks.append(m_im.copy())
                        mask_valid.append(True)
                except Exception as e:
                    raise IOError(f"Failed to read mask file {m_path}: {e}") from e
            else:
                # Annotation absent
                raw_masks.append(None)
                mask_valid.append(False)

        # Apply synchronized transformations
        img_tensor, masks_tensor = self.transform(image, raw_masks, mask_valid)
        mask_valid_tensor = torch.tensor(mask_valid, dtype=torch.bool)

        return {
            "image": img_tensor,
            "masks": masks_tensor,
            "mask_valid": mask_valid_tensor,
            "image_id": img_id,
        }


def split_idrid_dataset(
    root_dir: Union[str, Path],
    val_fraction: float = 0.2,
    seed: int = 42,
) -> Tuple[List[str], List[str], List[str]]:
    """Splits IDRiD images at the patient/original-image level to avoid data leakage.

    The official 54 training images are split into train and validation sets
    using a fixed seed. The official 27 testing images are kept strictly as
    the held-out test split.

    Args:
        root_dir: Base IDRiD directory.
        val_fraction: Fraction of training images to allocate to validation.
        seed: Random seed for exact reproducibility.

    Returns:
        (train_ids, val_ids, test_ids): Lists of image ID strings.
    """
    root_path = Path(root_dir)
    seg_root = root_path / "A. Segmentation" if (root_path / "A. Segmentation").exists() else root_path
    train_dir = seg_root / "1. Original Images" / "a. Training Set"
    test_dir = seg_root / "1. Original Images" / "b. Testing Set"

    if not train_dir.exists():
        raise FileNotFoundError(f"Training images directory not found at: {train_dir}")

    train_files = sorted([f for f in os.listdir(train_dir) if f.lower().endswith((".jpg", ".jpeg"))])
    train_all_ids = [os.path.splitext(f)[0] for f in train_files]

    # Deterministic split with fixed random seed
    rng = random.Random(seed)
    shuffled_ids = train_all_ids.copy()
    rng.shuffle(shuffled_ids)

    n_val = max(1, int(round(len(shuffled_ids) * val_fraction)))
    val_ids = sorted(shuffled_ids[:n_val])
    train_ids = sorted(shuffled_ids[n_val:])

    # Test IDs from official benchmark test set
    test_ids: List[str] = []
    if test_dir.exists():
        test_files = sorted([f for f in os.listdir(test_dir) if f.lower().endswith((".jpg", ".jpeg"))])
        test_ids = [os.path.splitext(f)[0] for f in test_files]

    # Verification: Zero leakage guarantee
    assert len(set(train_ids).intersection(set(val_ids))) == 0, "Data leakage detected between train and val!"
    assert len(set(train_ids).intersection(set(test_ids))) == 0, "Data leakage detected between train and test!"
    assert len(set(val_ids).intersection(set(test_ids))) == 0, "Data leakage detected between val and test!"

    return train_ids, val_ids, test_ids


def create_segmentation_dataloaders(
    root_dir: Union[str, Path],
    batch_size: int = 4,
    val_fraction: float = 0.2,
    seed: int = 42,
    img_size: Tuple[int, int] = (512, 512),
    classes: Sequence[str] = LESION_CLASSES,
    num_workers: int = 0,
    pin_memory: bool = False,
) -> Dict[str, DataLoader]:
    """Factory creating PyTorch DataLoaders for train, val, and test splits.

    Args:
        root_dir: Path to IDRiD or 'A. Segmentation' root.
        batch_size: Batch size for loaders.
        val_fraction: Fraction of training set allocated to validation.
        seed: Random seed for deterministic image-level split.
        img_size: Target image dimensions (H, W).
        classes: Target lesion classes ('MA', 'HE', 'EX', 'SE').
        num_workers: Number of worker subprocesses (default 0 for Windows safety).
        pin_memory: Whether DataLoader pins host memory for CUDA transfer.

    Returns:
        Dict with keys 'train', 'val', 'test' containing corresponding DataLoader instances.
    """
    train_ids, val_ids, test_ids = split_idrid_dataset(
        root_dir=root_dir,
        val_fraction=val_fraction,
        seed=seed,
    )

    # Train dataset (with augmentation)
    train_dataset = IDRiDDataset(
        root_dir=root_dir,
        split="train",
        image_ids=train_ids,
        classes=classes,
        img_size=img_size,
        is_train=True,
    )

    # Validation dataset (no augmentation)
    val_dataset = IDRiDDataset(
        root_dir=root_dir,
        split="train",
        image_ids=val_ids,
        classes=classes,
        img_size=img_size,
        is_train=False,
    )

    # Test dataset (held-out test set, no augmentation)
    test_dataset = IDRiDDataset(
        root_dir=root_dir,
        split="test",
        image_ids=test_ids,
        classes=classes,
        img_size=img_size,
        is_train=False,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=False,
    )

    return {
        "train": train_loader,
        "val": val_loader,
        "test": test_loader,
    }


class IDRiDPatchDataset(Dataset):
    """PyTorch Dataset for high-resolution lesion-centered IDRiD patches.

    Loads pre-extracted 256x256 image patches and corresponding multi-class lesion masks.
    Integrates seamlessly with existing training, metric tracking, and loss computation.
    """

    def __init__(
        self,
        patch_dir: Union[str, Path] = "data/processed/IDRiD_patches",
        split: str = "train",
        classes: Sequence[str] = LESION_CLASSES,
        is_train: bool = True,
    ) -> None:
        self.patch_dir = Path(patch_dir)
        if not self.patch_dir.is_absolute():
            self.patch_dir = PROJECT_ROOT / self.patch_dir

        self.split = split
        self.classes = list(classes)
        self.is_train = is_train

        meta_file = self.patch_dir / "metadata.json"
        if not meta_file.exists():
            raise FileNotFoundError(f"Patch metadata not found at {meta_file}. Run scripts/prepare_patches.py first.")

        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        if split not in metadata["splits"]:
            raise ValueError(f"Split '{split}' not found in metadata. Available: {list(metadata['splits'].keys())}")

        self.patches = metadata["splits"][split]["patches"]
        self.mean = torch.tensor(DEFAULT_IMAGENET_MEAN, dtype=torch.float32).view(3, 1, 1)
        self.std = torch.tensor(DEFAULT_IMAGENET_STD, dtype=torch.float32).view(3, 1, 1)

    def __len__(self) -> int:
        return len(self.patches)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        info = self.patches[idx]
        img_path = Path(info["image_path"])
        if not img_path.is_absolute():
            img_path = PROJECT_ROOT / img_path

        with Image.open(img_path) as im:
            img = im.convert("RGB")

        # Convert to tensor and normalize
        img_np = np.array(img, dtype=np.float32) / 255.0  # (H, W, 3)
        img_tensor = torch.from_numpy(img_np).permute(2, 0, 1)  # (3, H, W)
        img_tensor = (img_tensor - self.mean) / self.std

        # Load masks
        mask_arrays = np.zeros((len(self.classes), 256, 256), dtype=np.float32)
        mask_valid_list = []

        for c_idx, c_name in enumerate(self.classes):
            is_valid = info["mask_valid"].get(c_name, False)
            mask_valid_list.append(is_valid)

            if is_valid and info["mask_paths"].get(c_name) is not None:
                m_path = Path(info["mask_paths"][c_name])
                if not m_path.is_absolute():
                    m_path = PROJECT_ROOT / m_path
                if m_path.exists():
                    with Image.open(m_path) as m_im:
                        m_np = np.array(m_im, dtype=np.float32)
                        mask_arrays[c_idx] = (m_np > 127).astype(np.float32)

        masks_tensor = torch.from_numpy(mask_arrays)
        mask_valid_tensor = torch.tensor(mask_valid_list, dtype=torch.bool)

        # Synchronized horizontal & vertical flip augmentations during training
        if self.is_train:
            if random.random() > 0.5:
                img_tensor = torch.flip(img_tensor, dims=[2])
                masks_tensor = torch.flip(masks_tensor, dims=[2])
            if random.random() > 0.5:
                img_tensor = torch.flip(img_tensor, dims=[1])
                masks_tensor = torch.flip(masks_tensor, dims=[1])

        return {
            "image": img_tensor,
            "masks": masks_tensor,
            "mask_valid": mask_valid_tensor,
            "image_id": info["patch_id"],
            "parent_id": info["parent_id"],
        }


def create_patch_dataloaders(
    patch_dir: Union[str, Path] = "data/processed/IDRiD_patches",
    batch_size: int = 8,
    classes: Sequence[str] = LESION_CLASSES,
    num_workers: int = 0,
) -> Dict[str, DataLoader]:
    """Creates training and validation DataLoaders for IDRiD lesion patches."""
    train_dataset = IDRiDPatchDataset(
        patch_dir=patch_dir,
        split="train",
        classes=classes,
        is_train=True,
    )
    val_dataset = IDRiDPatchDataset(
        patch_dir=patch_dir,
        split="val",
        classes=classes,
        is_train=False,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        drop_last=False,
    )
    return {"train": train_loader, "val": val_loader}

