"""Inference entry point for lesion segmentation conforming to integration contract."""

from pathlib import Path
from typing import Any, Dict, Optional, Union
from src.vision.segmentation.predict import segment_lesions as _segment_lesions


def segment_lesions(
    image_path: Optional[Union[str, Path, Any]] = None,
    checkpoint_path: Optional[Union[str, Path]] = None,
    config: Optional[Any] = None,
    output_dir: Optional[Union[str, Path]] = "storage/segmentation_masks",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Segment diabetic retinopathy lesions from a retinal fundus photograph.

    Args:
        image_path: Path to the retinal fundus image, PIL Image, or numpy array.
        checkpoint_path: Optional path to model weights checkpoint.
        config: Optional SegmentationConfig overrides.
        output_dir: Directory where masks and overlays will be stored.

    Returns:
        Structured result dict matching docs/integration_contract.md.
    """
    img = image_path if image_path is not None else kwargs.get("image_input")
    return _segment_lesions(
        image_input=img,
        checkpoint_path=checkpoint_path,
        config=config,
        output_dir=output_dir,
    )


__all__ = ["segment_lesions"]
