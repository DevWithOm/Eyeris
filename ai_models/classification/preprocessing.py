"""
Diabetic Retinopathy Classification Preprocessing Pipeline.

Implements retinal border cropping, resizing, and ImageNet tensor normalization
identical to the APTOS 2019 training pipeline verified in historical project configs.
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image
import torch
from torchvision import transforms

# Verified standard ImageNet normalization constants used during training
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
DEFAULT_IMAGE_SIZE = 224
DEFAULT_CROP_TOLERANCE = 10
MIN_CROP_DIMENSION = 50


def crop_fundus_borders(image: Image.Image, tol: int = DEFAULT_CROP_TOLERANCE) -> Image.Image:
    """
    Detects and crops black outer margins from retinal fundus photographs.
    
    Verified implementation from historical training source (origin/Shourya-Thorat:src/data.py
    and configs/default.yaml where crop_borders=True):
    - Identifies non-background pixels where max intensity across color channels > tol (default 10).
    - Obtains bounding rectangle [xmin, ymin, xmax, ymax] of retinal tissue.
    - Guards against degenerate crops (< 50px dimension) or blank images.

    Args:
        image: PIL Image (RGB or Grayscale).
        tol: Pixel intensity threshold to distinguish foreground retina from dark border.

    Returns:
        PIL.Image: Cropped image focused on retinal tissue.
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

    ymin, ymax = int(row_nonzero[0]), int(row_nonzero[-1])
    xmin, xmax = int(col_nonzero[0]), int(col_nonzero[-1])

    # Prevent degenerate crops on abnormal or severely occluded images
    if (ymax - ymin < MIN_CROP_DIMENSION) or (xmax - xmin < MIN_CROP_DIMENSION):
        return image

    return image.crop((xmin, ymin, xmax, ymax))


def get_inference_transforms(image_size: int = DEFAULT_IMAGE_SIZE) -> transforms.Compose:
    """
    Returns deterministic validation and inference transforms:
    1. Resize to (image_size, image_size) with bilinear interpolation.
    2. Convert PIL Image to PyTorch FloatTensor in range [0.0, 1.0].
    3. Normalize with ImageNet channel mean and standard deviation.
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def preprocess_fundus_image(
    image_input: Union[str, Path, Image.Image, np.ndarray],
    image_size: int = DEFAULT_IMAGE_SIZE,
    crop_borders: bool = True,
    crop_tolerance: int = DEFAULT_CROP_TOLERANCE,
    transform: Optional[transforms.Compose] = None,
) -> torch.Tensor:
    """
    Full inference preprocessing pipeline for a single retinal fundus image.

    Steps:
      1. Load file path / array and convert to PIL Image in RGB format.
      2. Optionally crop black camera borders (matching training config).
      3. Apply deterministic resize and ImageNet tensor normalization.
      4. Add batch dimension: shape [1, 3, image_size, image_size].

    Args:
        image_input: File path (str/Path), PIL Image, or NumPy RGB array.
        image_size: Target square dimension (224 for EfficientNet-B0).
        crop_borders: Whether to crop peripheral dark borders (default True).
        crop_tolerance: Threshold for border detection (default 10).
        transform: Optional custom torchvision transform.

    Returns:
        torch.Tensor: Preprocessed tensor of shape [1, 3, image_size, image_size].
    """
    # 1. Format normalization to PIL Image (RGB)
    if isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.exists():
            raise FileNotFoundError(f"Image not found at path: {path}")
        img = Image.open(path).convert("RGB")
    elif isinstance(image_input, np.ndarray):
        img = Image.fromarray(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    # 2. Retinal border cropping
    if crop_borders:
        img = crop_fundus_borders(img, tol=crop_tolerance)

    # 3. Transform & normalize
    if transform is None:
        transform = get_inference_transforms(image_size=image_size)

    tensor: torch.Tensor = transform(img)

    # 4. Batch dimension [1, 3, H, W]
    return tensor.unsqueeze(0)