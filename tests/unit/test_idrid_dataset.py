"""Unit tests for IDRiD retinal lesion dataset preparation pipeline."""

import os
from pathlib import Path
import pytest
import torch
from PIL import Image

from ai_models.segmentation.dataset import (
    IDRiDDataset,
    LESION_CLASSES,
    SynchronizedTransform,
    create_segmentation_dataloaders,
    split_idrid_dataset,
)

DATASET_ROOT = Path("data/raw/IDRiD")


@pytest.fixture
def dataset_available() -> bool:
    """Check if the extracted IDRiD dataset is available."""
    seg_path = DATASET_ROOT / "A. Segmentation" / "1. Original Images" / "a. Training Set"
    return seg_path.exists()


def test_dataset_initialization(dataset_available: bool):
    """Test standard initialization of train and test datasets."""
    if not dataset_available:
        pytest.skip("IDRiD dataset not available in data/raw/IDRiD")

    train_ds = IDRiDDataset(root_dir=DATASET_ROOT, split="train", is_train=False)
    test_ds = IDRiDDataset(root_dir=DATASET_ROOT, split="test", is_train=False)

    assert len(train_ds) == 54, f"Expected 54 training images, found {len(train_ds)}"
    assert len(test_ds) == 27, f"Expected 27 testing images, found {len(test_ds)}"
    assert train_ds.classes == LESION_CLASSES


def test_image_mask_correspondence(dataset_available: bool):
    """Test image-mask correspondence across samples."""
    if not dataset_available:
        pytest.skip("IDRiD dataset not available in data/raw/IDRiD")

    ds = IDRiDDataset(root_dir=DATASET_ROOT, split="train", is_train=False)
    for idx in range(min(5, len(ds))):
        sample = ds[idx]
        image_id = sample["image_id"]
        assert isinstance(image_id, str)
        assert image_id.startswith("IDRiD_")

        # Verify corresponding sample entry in index
        raw_sample = ds.samples[idx]
        assert raw_sample["image_id"] == image_id
        assert Path(str(raw_sample["image_path"])).stem == image_id


def test_tensor_dimensions(dataset_available: bool):
    """Test output tensor dimensions and channels for different target sizes."""
    if not dataset_available:
        pytest.skip("IDRiD dataset not available in data/raw/IDRiD")

    target_size = (256, 384)  # (H, W)
    ds = IDRiDDataset(
        root_dir=DATASET_ROOT,
        split="train",
        img_size=target_size,
        is_train=False,
    )

    sample = ds[0]
    image = sample["image"]
    masks = sample["masks"]
    mask_valid = sample["mask_valid"]

    assert isinstance(image, torch.Tensor)
    assert isinstance(masks, torch.Tensor)
    assert isinstance(mask_valid, torch.Tensor)

    # Image: (3, H, W)
    assert image.shape == (3, target_size[0], target_size[1])
    # Masks: (4, H, W) -> MA, HE, EX, SE
    assert masks.shape == (4, target_size[0], target_size[1])
    # Validity flags: (4,)
    assert mask_valid.shape == (4,)
    assert mask_valid.dtype == torch.bool


def test_mask_binary_values(dataset_available: bool):
    """Ensure nearest-neighbor interpolation maintains strict binary {0.0, 1.0} values."""
    if not dataset_available:
        pytest.skip("IDRiD dataset not available in data/raw/IDRiD")

    ds = IDRiDDataset(
        root_dir=DATASET_ROOT,
        split="train",
        img_size=(256, 256),
        is_train=True,  # Augmentations enabled
    )

    # Check across multiple augmented samples
    for idx in range(min(5, len(ds))):
        sample = ds[idx]
        masks = sample["masks"]
        unique_vals = torch.unique(masks).tolist()
        for val in unique_vals:
            assert val in (0.0, 1.0), f"Non-binary mask value {val} detected in sample {sample['image_id']}"


def test_missing_annotation_handling(dataset_available: bool):
    """Verify that absent annotations are tracked cleanly via mask_valid and not falsely assumed negative."""
    if not dataset_available:
        pytest.skip("IDRiD dataset not available in data/raw/IDRiD")

    train_ds = IDRiDDataset(root_dir=DATASET_ROOT, split="train", is_train=False)

    # 1. Test IDRiD_43 which has NO Haemorrhages (_HE.tif)
    idrid_43_idx = next(i for i, s in enumerate(train_ds.samples) if s["image_id"] == "IDRiD_43")
    sample_43 = train_ds[idrid_43_idx]

    he_idx = LESION_CLASSES.index("HE")
    assert sample_43["mask_valid"][he_idx].item() is False, "IDRiD_43 HE should be marked invalid/missing"
    assert torch.all(sample_43["masks"][he_idx] == 0.0), "Missing HE mask should default to zero tensor"

    # 2. Test IDRiD_01 which has NO Soft Exudates (_SE.tif)
    idrid_01_idx = next(i for i, s in enumerate(train_ds.samples) if s["image_id"] == "IDRiD_01")
    sample_01 = train_ds[idrid_01_idx]

    se_idx = LESION_CLASSES.index("SE")
    assert sample_01["mask_valid"][se_idx].item() is False, "IDRiD_01 SE should be marked invalid/missing"

    # 3. Test IDRiD_03 which DOES have Soft Exudates (_SE.tif)
    idrid_03_idx = next(i for i, s in enumerate(train_ds.samples) if s["image_id"] == "IDRiD_03")
    sample_03 = train_ds[idrid_03_idx]
    assert sample_03["mask_valid"][se_idx].item() is True, "IDRiD_03 SE should be marked present/valid"
    assert sample_03["masks"][se_idx].sum() > 0, "IDRiD_03 SE should contain foreground lesion pixels"


def test_reproducible_split_no_leakage(dataset_available: bool):
    """Verify that dataset splits are reproducible and have zero data leakage."""
    if not dataset_available:
        pytest.skip("IDRiD dataset not available in data/raw/IDRiD")

    train_ids_1, val_ids_1, test_ids_1 = split_idrid_dataset(DATASET_ROOT, val_fraction=0.2, seed=42)
    train_ids_2, val_ids_2, test_ids_2 = split_idrid_dataset(DATASET_ROOT, val_fraction=0.2, seed=42)

    # Determinism
    assert train_ids_1 == train_ids_2
    assert val_ids_1 == val_ids_2
    assert test_ids_1 == test_ids_2

    # Zero data leakage guarantees
    set_train = set(train_ids_1)
    set_val = set(val_ids_1)
    set_test = set(test_ids_1)

    assert len(set_train.intersection(set_val)) == 0, "Leakage between train and val"
    assert len(set_train.intersection(set_test)) == 0, "Leakage between train and test"
    assert len(set_val.intersection(set_test)) == 0, "Leakage between val and test"

    # Expected counts
    assert len(set_train) + len(set_val) == 54
    assert len(set_test) == 27


def test_synchronized_transform():
    """Unit test for SynchronizedTransform verifying geometric alignment."""
    transform = SynchronizedTransform(img_size=(100, 100), is_train=False)

    # Create synthetic image with bright quadrant (top-left)
    img = Image.new("RGB", (200, 200), color=(0, 0, 0))
    for x in range(50):
        for y in range(50):
            img.putpixel((x, y), (255, 255, 255))

    # Create synthetic mask with marked region (top-left)
    mask = Image.new("L", (200, 200), color=0)
    for x in range(50):
        for y in range(50):
            mask.putpixel((x, y), 1)

    img_tensor, mask_tensor = transform(img, [mask], [True])

    assert img_tensor.shape == (3, 100, 100)
    assert mask_tensor.shape == (1, 100, 100)

    # In top-left corner, mask must be foreground 1.0
    assert mask_tensor[0, 10, 10].item() == 1.0
    # In bottom-right corner, mask must be background 0.0
    assert mask_tensor[0, 90, 90].item() == 0.0


def test_dataloader_batch_generation(dataset_available: bool):
    """Test DataLoader batching and collating."""
    if not dataset_available:
        pytest.skip("IDRiD dataset not available in data/raw/IDRiD")

    loaders = create_segmentation_dataloaders(
        root_dir=DATASET_ROOT,
        batch_size=3,
        val_fraction=0.2,
        seed=42,
        img_size=(256, 256),
    )

    assert "train" in loaders and "val" in loaders and "test" in loaders

    batch = next(iter(loaders["train"]))
    images = batch["image"]
    masks = batch["masks"]
    mask_valid = batch["mask_valid"]
    image_ids = batch["image_id"]

    assert images.shape == (3, 3, 256, 256)
    assert masks.shape == (3, 4, 256, 256)
    assert mask_valid.shape == (3, 4)
    assert len(image_ids) == 3


def test_error_handling_invalid_inputs():
    """Verify informative errors on invalid configurations."""
    with pytest.raises(ValueError, match="Unsupported lesion class"):
        IDRiDDataset(root_dir=DATASET_ROOT, classes=["INVALID_CLASS"])

    with pytest.raises(FileNotFoundError, match="Cannot locate IDRiD Segmentation directory"):
        IDRiDDataset(root_dir="non_existent_directory_xyz")

