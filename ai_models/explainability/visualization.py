"""
Visualization helpers for Explainable AI (Grad-CAM) in retinal fundus screening.

Provides routines to resize, colormap, overlay, and persist saliency maps onto original retinal images
with exact spatial alignment and support for border-cropped fundus photographs.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import matplotlib
import matplotlib.cm as cm
import numpy as np
from PIL import Image


def colorize_heatmap(
    heatmap: np.ndarray,
    colormap_name: str = "jet"
) -> Image.Image:
    """
    Converts a 2D normalized float heatmap [0.0, 1.0] into an RGB PIL Image
    using the specified matplotlib colormap.

    Args:
        heatmap: 2D numpy array of floats (H, W).
        colormap_name: Matplotlib colormap string (e.g. 'jet', 'turbo', 'viridis').

    Returns:
        RGB PIL Image of the colorized heatmap.
    """
    heatmap_clipped = np.clip(heatmap, 0.0, 1.0)

    try:
        cmap = matplotlib.colormaps[colormap_name]
    except (AttributeError, KeyError):
        cmap = cm.get_cmap(colormap_name)

    # cmap output is (H, W, 4) in [0.0, 1.0]
    rgba = cmap(heatmap_clipped)
    rgb = (rgba[:, :, :3] * 255.0).astype(np.uint8)

    return Image.fromarray(rgb, mode="RGB")


def project_heatmap_to_original(
    heatmap: np.ndarray,
    original_size: Tuple[int, int],
    crop_box: Optional[Tuple[int, int, int, int]] = None
) -> np.ndarray:
    """
    Projects a Grad-CAM heatmap computed on a cropped fundus region back to the original full image coordinates.
    Areas outside the crop_box receive 0.0 (no activation).

    Args:
        heatmap: 2D numpy array of normalized Grad-CAM values [0.0, 1.0].
        original_size: Tuple of (original_width, original_height).
        crop_box: Tuple of (xmin, ymin, xmax, ymax) used when cropping the original image.
                  If None, returns the heatmap as-is.

    Returns:
        2D numpy array of shape (original_height, original_width) in [0.0, 1.0].
    """
    if crop_box is None:
        return heatmap

    orig_width, orig_height = original_size
    xmin, ymin, xmax, ymax = crop_box
    crop_w = xmax - xmin
    crop_h = ymax - ymin

    # Resize heatmap to match the cropped region exactly
    heatmap_pil = Image.fromarray(heatmap.astype(np.float32))
    heatmap_crop_resized = heatmap_pil.resize((crop_w, crop_h), resample=Image.Resampling.BILINEAR)
    crop_arr = np.array(heatmap_crop_resized, dtype=np.float32)

    # Place inside full canvas matching the original dimensions
    full_heatmap = np.zeros((orig_height, orig_width), dtype=np.float32)
    full_heatmap[ymin:ymax, xmin:xmax] = crop_arr
    return full_heatmap


def overlay_heatmap_on_image(
    image: Union[str, Path, Image.Image, np.ndarray],
    heatmap: np.ndarray,
    alpha: float = 0.4,
    colormap_name: str = "jet",
    crop_box: Optional[Tuple[int, int, int, int]] = None
) -> Tuple[Image.Image, Image.Image, Image.Image]:
    """
    Overlays a Grad-CAM heatmap onto the original or cropped retinal image with exact spatial alignment.

    Args:
        image: Original or cropped fundus image as a file path, PIL Image, or uint8 NumPy array (H, W, 3).
        heatmap: 2D numpy array with values in [0.0, 1.0].
        alpha: Blending weight for the heatmap overlay (0.0 = only original image, 1.0 = only heatmap).
        colormap_name: Colormap to use (default: 'jet').
        crop_box: Optional bounding box (xmin, ymin, xmax, ymax) if image is uncropped and heatmap was
                  computed on a cropped region.

    Returns:
        Tuple of (base_image_pil, colorized_heatmap_pil, blended_overlay_pil)
        All returned images have the exact dimensions of the base image.

    Raises:
        ValueError: If alpha is out of range [0.0, 1.0] or heatmap is not a 2D array.
    """
    if not (0.0 <= alpha <= 1.0):
        raise ValueError(f"Alpha must be between 0.0 and 1.0, got {alpha}")

    if not isinstance(heatmap, np.ndarray) or heatmap.ndim != 2:
        raise ValueError(f"Heatmap must be a 2D numpy array, got shape {getattr(heatmap, 'shape', type(heatmap))}")

    # 1. Load / standardize image
    if isinstance(image, (str, Path)):
        orig_pil = Image.open(image).convert("RGB")
    elif isinstance(image, np.ndarray):
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        orig_pil = Image.fromarray(image).convert("RGB")
    elif isinstance(image, Image.Image):
        orig_pil = image.convert("RGB")
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    orig_width, orig_height = orig_pil.size

    # 2. If crop_box is provided, project heatmap back to the full image coordinates
    if crop_box is not None:
        aligned_heatmap = project_heatmap_to_original(heatmap, (orig_width, orig_height), crop_box)
    else:
        aligned_heatmap = heatmap

    # 3. Resize heatmap to match base image dimensions
    heatmap_pil = Image.fromarray(aligned_heatmap.astype(np.float32))
    heatmap_resized = heatmap_pil.resize((orig_width, orig_height), resample=Image.Resampling.BILINEAR)
    heatmap_resized_np = np.array(heatmap_resized, dtype=np.float32)

    # 4. Apply color map to resized heatmap
    heatmap_colored_pil = colorize_heatmap(heatmap_resized_np, colormap_name=colormap_name)

    # 5. Blend base image and colorized heatmap
    blended_overlay_pil = Image.blend(orig_pil, heatmap_colored_pil, alpha=alpha)

    return orig_pil, heatmap_colored_pil, blended_overlay_pil


def save_explanation_artifacts(
    output_dir: Union[str, Path],
    prefix: str,
    original: Image.Image,
    heatmap_colored: Image.Image,
    overlay: Image.Image,
    heatmap_raw: Optional[np.ndarray] = None
) -> Dict[str, str]:
    """
    Persists original image, colorized heatmap, composite overlay, and optional raw heatmap
    to the designated output directory.

    Args:
        output_dir: Destination folder path.
        prefix: Case or screening identifier prefix for filenames (e.g. 'case_001').
        original: Base retinal image (PIL).
        heatmap_colored: Colorized heatmap (PIL).
        overlay: Blended overlay image (PIL).
        heatmap_raw: Optional raw 2D numpy array of normalized Grad-CAM values.

    Returns:
        Dict mapping artifact keys ('original', 'heatmap', 'overlay', 'raw_npy') to saved file paths.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    saved_files: Dict[str, str] = {}

    orig_file = out_path / f"{prefix}_original.png"
    original.save(orig_file, format="PNG")
    saved_files["original"] = str(orig_file.resolve())

    heatmap_file = out_path / f"{prefix}_heatmap.png"
    heatmap_colored.save(heatmap_file, format="PNG")
    saved_files["heatmap"] = str(heatmap_file.resolve())

    overlay_file = out_path / f"{prefix}_overlay.png"
    overlay.save(overlay_file, format="PNG")
    saved_files["overlay"] = str(overlay_file.resolve())

    if heatmap_raw is not None:
        raw_file = out_path / f"{prefix}_heatmap_raw.npy"
        np.save(raw_file, heatmap_raw.astype(np.float32))
        saved_files["raw_npy"] = str(raw_file.resolve())

    return saved_files
