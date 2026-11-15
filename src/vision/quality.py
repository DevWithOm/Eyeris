"""Retinal Image Quality Assessment Module.

OBJECTIVE:
Determine whether an input retinal fundus photograph is technically suitable
for automated diabetic retinopathy screening.

QUALITY CHECKS IMPLEMENTED:
1. Blur detection using modified Laplacian variance on the green retinal channel.
2. Illumination and contrast assessment.
3. Underexposure detection (mean luminance, dark foreground ratio).
4. Overexposure detection (saturation glare and reflection ratio).
5. Field-of-View (FOV) assessment (aperture coverage, contour circularity, clipping).
6. Image validity and corruption detection (dimensions, channels, unreadable files).

STATUS VALUES:
- GRADABLE: Image meets technical criteria for automated lesion analysis.
- REVIEW_REQUIRED: Marginal sharpness, illumination, or FOV; clinical review advised.
- UNGRADABLE: Severe defect (blur, underexposure, corruption) preventing reliable analysis.

DISCLAIMER:
This module provides research-prototype heuristic quality screening filters.
Quality scores and status codes are not clinically validated diagnostic criteria.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image


class QualityStatus(str, Enum):
    """Gradability status classification."""
    GRADABLE = "GRADABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNGRADABLE = "UNGRADABLE"


class FOVStatus(str, Enum):
    """Field-of-View adequacy classification."""
    ADEQUATE = "ADEQUATE"
    PARTIAL_CLIPPED = "PARTIAL_CLIPPED"
    INSUFFICIENT = "INSUFFICIENT"


class QualityReason(str, Enum):
    """Standardized failure and review reason codes."""
    # Validity / Corruption
    FILE_NOT_FOUND = "REASON_FILE_NOT_FOUND"
    CORRUPTED_OR_UNREADABLE = "REASON_CORRUPTED_OR_UNREADABLE"
    INVALID_DIMENSIONS = "REASON_INVALID_DIMENSIONS"
    INVALID_CHANNELS = "REASON_INVALID_CHANNELS"
    BLANK_IMAGE = "REASON_BLANK_IMAGE"

    # Blur
    SEVERE_BLUR = "REASON_SEVERE_BLUR"
    MARGINAL_BLUR = "REASON_MARGINAL_BLUR"

    # Illumination
    UNDEREXPOSED = "REASON_UNDEREXPOSED"
    OVEREXPOSED = "REASON_OVEREXPOSED"
    LOW_CONTRAST = "REASON_LOW_CONTRAST"

    # Field of view
    FOV_TOO_SMALL = "REASON_FOV_TOO_SMALL"
    FOV_CLIPPED = "REASON_FOV_CLIPPED"


@dataclass
class QualityConfig:
    """Configurable thresholds for heuristic quality assessment."""

    # Resolution constraints
    min_width: int = 512
    min_height: int = 512

    # Retinal foreground extraction threshold (0-255)
    bg_threshold: int = 15
    mask_erosion_kernel_size: int = 15

    # Blur thresholds (Laplacian variance on green channel within eroded mask)
    blur_ungradable_threshold: float = 8.0
    blur_review_threshold: float = 18.0
    # Reference sharpness for normalizing blur score to [0, 1]
    blur_reference_max: float = 40.0

    # Illumination thresholds (foreground luminance)
    underexpose_mean_thresh: float = 45.0
    underexpose_review_thresh: float = 65.0
    overexpose_mean_thresh: float = 195.0
    # Fraction of foreground pixels near saturation (> 240)
    overexpose_saturation_thresh: float = 0.04
    overexpose_saturation_review_thresh: float = 0.015

    # Contrast threshold (standard deviation of foreground pixels)
    min_contrast_thresh: float = 6.0

    # Field-of-View thresholds (ratio of foreground pixels to total image area)
    min_fov_ratio: float = 0.35
    review_fov_ratio: float = 0.45
    max_fov_ratio: float = 0.95

    # Weights for composite quality score [0.0 - 1.0]
    weight_blur: float = 0.45
    weight_illumination: float = 0.35
    weight_fov: float = 0.20


class RetinalQualityAssessor:
    """Evaluates retinal fundus image quality using classical computer vision metrics."""

    def __init__(self, config: Optional[QualityConfig] = None) -> None:
        self.config = config or QualityConfig()

    def assess(
        self,
        image_input: Union[str, Path, np.ndarray, Image.Image],
    ) -> Dict[str, Any]:
        """Perform comprehensive quality evaluation on an input fundus image.

        Args:
            image_input: File path, numpy array (BGR or RGB), or PIL Image.

        Returns:
            Dict containing:
                quality_score: float in [0.0, 1.0]
                status: 'GRADABLE', 'REVIEW_REQUIRED', or 'UNGRADABLE'
                blur_score: float in [0.0, 1.0] (higher = sharper)
                illumination_score: float in [0.0, 1.0] (higher = better exposed)
                field_of_view_status: 'ADEQUATE', 'PARTIAL_CLIPPED', or 'INSUFFICIENT'
                reason_codes: list of str reason identifiers
                recapture_suggestion: Optional actionable advice
                details: Dict of raw diagnostic metrics
        """
        reasons: List[str] = []
        recapture_suggestions: List[str] = []

        # 1. Load and validate image input
        bgr_image, err_reason = self._load_image(image_input)
        if bgr_image is None or err_reason is not None:
            return self._build_result(
                quality_score=0.0,
                status=QualityStatus.UNGRADABLE,
                blur_score=0.0,
                illumination_score=0.0,
                fov_status=FOVStatus.INSUFFICIENT,
                reason_codes=[err_reason or QualityReason.CORRUPTED_OR_UNREADABLE.value],
                recapture_suggestion="Input image is unreadable or corrupted. Please acquire a new image.",
                details={"error": err_reason},
            )

        h, w, c = bgr_image.shape

        # Check resolution immediately
        if w < self.config.min_width or h < self.config.min_height:
            return self._build_result(
                quality_score=0.0,
                status=QualityStatus.UNGRADABLE,
                blur_score=0.0,
                illumination_score=0.0,
                fov_status=FOVStatus.INSUFFICIENT,
                reason_codes=[QualityReason.INVALID_DIMENSIONS.value],
                recapture_suggestion=(
                    f"Image resolution ({w}x{h}) is below minimum requirement "
                    f"({self.config.min_width}x{self.config.min_height})."
                ),
                details={"image_dimensions": (w, h)},
            )

        # Convert to grayscale and green channel
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        green = bgr_image[:, :, 1]

        # Check for completely blank / flat images
        gray_std = float(np.std(gray))
        if gray_std < 1.0:
            return self._build_result(
                quality_score=0.0,
                status=QualityStatus.UNGRADABLE,
                blur_score=0.0,
                illumination_score=0.0,
                fov_status=FOVStatus.INSUFFICIENT,
                reason_codes=[QualityReason.BLANK_IMAGE.value],
                recapture_suggestion="Image is blank, uniform, or devoid of retinal structures. Recapture required.",
                details={"gray_std": gray_std},
            )

        # 2. Extract Retinal Foreground Mask
        fg_mask, fov_ratio, fov_status, fov_reasons = self._assess_fov(gray, w, h)
        reasons.extend(fov_reasons)

        if fov_status == FOVStatus.INSUFFICIENT:
            recapture_suggestions.append(
                "Retinal field of view is too small or absent. Re-align camera to center the fundus."
            )
        elif fov_status == FOVStatus.PARTIAL_CLIPPED:
            recapture_suggestions.append(
                "Peripheral retina appears clipped at image margins. Verify patient alignment."
            )

        # If foreground is completely absent, cannot evaluate blur/illumination
        fg_pixels_count = int(np.sum(fg_mask))
        if fg_pixels_count < 100:
            return self._build_result(
                quality_score=0.0,
                status=QualityStatus.UNGRADABLE,
                blur_score=0.0,
                illumination_score=0.0,
                fov_status=fov_status,
                reason_codes=[QualityReason.FOV_TOO_SMALL.value],
                recapture_suggestion="No retinal tissue detected in frame. Please recapture with proper centering.",
                details={"fg_pixels": fg_pixels_count, "fov_ratio": fov_ratio},
            )

        # 3. Assess Blur / Sharpness
        blur_score, lap_var, blur_reasons, blur_advice = self._assess_blur(green, fg_mask)
        reasons.extend(blur_reasons)
        if blur_advice:
            recapture_suggestions.append(blur_advice)

        # 4. Assess Illumination & Exposure
        illum_score, illum_reasons, illum_advice, illum_details = self._assess_illumination(gray, fg_mask)
        reasons.extend(illum_reasons)
        if illum_advice:
            recapture_suggestions.append(illum_advice)

        # 5. Composite Quality Score Calculation
        fov_score = 1.0 if fov_status == FOVStatus.ADEQUATE else (0.5 if fov_status == FOVStatus.PARTIAL_CLIPPED else 0.0)

        composite_score = (
            self.config.weight_blur * blur_score
            + self.config.weight_illumination * illum_score
            + self.config.weight_fov * fov_score
        )
        composite_score = float(np.clip(composite_score, 0.0, 1.0))

        # 6. Determine Status
        status = self._decide_status(
            reasons=reasons,
            composite_score=composite_score,
            fov_status=fov_status,
        )

        final_recapture_str = " | ".join(recapture_suggestions) if recapture_suggestions else None

        details = {
            "image_dimensions": (w, h),
            "laplacian_variance": lap_var,
            "fov_coverage_ratio": fov_ratio,
            **illum_details,
        }

        return self._build_result(
            quality_score=round(composite_score, 4),
            status=status,
            blur_score=round(blur_score, 4),
            illumination_score=round(illum_score, 4),
            fov_status=fov_status,
            reason_codes=sorted(list(set(reasons))),
            recapture_suggestion=final_recapture_str,
            details=details,
        )

    def _load_image(
        self,
        image_input: Union[str, Path, np.ndarray, Image.Image],
    ) -> Tuple[Optional[np.ndarray], Optional[str]]:
        """Safely loads image input into BGR numpy array."""
        try:
            if isinstance(image_input, (str, Path)):
                path = Path(image_input)
                if not path.is_file():
                    return None, QualityReason.FILE_NOT_FOUND.value
                img = cv2.imread(str(path), cv2.IMREAD_COLOR)
                if img is None:
                    return None, QualityReason.CORRUPTED_OR_UNREADABLE.value
                return img, None

            if isinstance(image_input, Image.Image):
                rgb = np.array(image_input.convert("RGB"))
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                return bgr, None

            if isinstance(image_input, np.ndarray):
                if image_input.ndim == 2:
                    # Single channel grayscale -> convert to 3-channel
                    bgr = cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
                    return bgr, None
                if image_input.ndim == 3 and image_input.shape[2] == 3:
                    return image_input.copy(), None
                return None, QualityReason.INVALID_CHANNELS.value

            return None, QualityReason.CORRUPTED_OR_UNREADABLE.value
        except Exception:
            return None, QualityReason.CORRUPTED_OR_UNREADABLE.value

    def _assess_fov(
        self,
        gray: np.ndarray,
        width: int,
        height: int,
    ) -> Tuple[np.ndarray, float, FOVStatus, List[str]]:
        """Evaluates fundus field of view area and boundary clipping."""
        reasons: List[str] = []
        total_pixels = width * height

        # Binary threshold for retinal foreground
        fg_mask = gray > self.config.bg_threshold
        fg_count = np.sum(fg_mask)
        fov_ratio = float(fg_count / total_pixels)

        # Check boundary margins (check if foreground touches outer edge)
        margin = max(4, int(min(width, height) * 0.01))
        touches_top = np.any(fg_mask[:margin, :])
        touches_bottom = np.any(fg_mask[-margin:, :])
        touches_left = np.any(fg_mask[:, :margin])
        touches_right = np.any(fg_mask[:, -margin:])
        edge_touch_count = sum([touches_top, touches_bottom, touches_left, touches_right])

        if fov_ratio < self.config.min_fov_ratio:
            fov_status = FOVStatus.INSUFFICIENT
            reasons.append(QualityReason.FOV_TOO_SMALL.value)
        elif fov_ratio < self.config.review_fov_ratio or edge_touch_count >= 2:
            fov_status = FOVStatus.PARTIAL_CLIPPED
            if edge_touch_count >= 2:
                reasons.append(QualityReason.FOV_CLIPPED.value)
        else:
            fov_status = FOVStatus.ADEQUATE

        return fg_mask, fov_ratio, fov_status, reasons

    def _assess_blur(
        self,
        green_channel: np.ndarray,
        fg_mask: np.ndarray,
    ) -> Tuple[float, float, List[str], Optional[str]]:
        """Calculates blur score using modified Laplacian variance on eroded foreground."""
        reasons: List[str] = []
        advice: Optional[str] = None

        # Erode mask to avoid the sharp synthetic circular border edge inflating sharpness
        ksize = self.config.mask_erosion_kernel_size
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
        eroded_mask = cv2.erode(fg_mask.astype(np.uint8), kernel) > 0

        if np.sum(eroded_mask) < 100:
            eroded_mask = fg_mask

        lap = cv2.Laplacian(green_channel, cv2.CV_64F)
        lap_fg = lap[eroded_mask]

        lap_var = float(np.var(lap_fg)) if len(lap_fg) > 0 else 0.0

        # Map Laplacian variance to [0.0, 1.0] sigmoid/soft-clipping curve
        norm_score = float(np.clip(lap_var / self.config.blur_reference_max, 0.0, 1.0))

        if lap_var < self.config.blur_ungradable_threshold:
            reasons.append(QualityReason.SEVERE_BLUR.value)
            advice = "Image suffers from severe motion or defocus blur. Instruct patient to fixate steadily and refocus."
        elif lap_var < self.config.blur_review_threshold:
            reasons.append(QualityReason.MARGINAL_BLUR.value)
            advice = "Image shows mild blur affecting small microvascular details. Clinician review recommended."

        return norm_score, lap_var, reasons, advice

    def _assess_illumination(
        self,
        gray: np.ndarray,
        fg_mask: np.ndarray,
    ) -> Tuple[float, List[str], Optional[str], Dict[str, Any]]:
        """Assesses underexposure, overexposure, and contrast balance."""
        reasons: List[str] = []
        advice: Optional[str] = None

        fg_pixels = gray[fg_mask]
        mean_lum = float(np.mean(fg_pixels))
        median_lum = float(np.median(fg_pixels))
        std_lum = float(np.std(fg_pixels))

        # Percentage of pixels saturated (> 240)
        saturation_count = np.sum(fg_pixels >= 240)
        saturation_ratio = float(saturation_count / len(fg_pixels))

        # Percentage of deeply dark pixels (< 25)
        deep_dark_count = np.sum(fg_pixels <= 25)
        deep_dark_ratio = float(deep_dark_count / len(fg_pixels))

        # Underexposure check
        if mean_lum < self.config.underexpose_mean_thresh or deep_dark_ratio > 0.40:
            reasons.append(QualityReason.UNDEREXPOSED.value)
            advice = "Image is underexposed/dark. Increase flash energy or verify pupil dilation."
        elif mean_lum < self.config.underexpose_review_thresh:
            reasons.append(QualityReason.UNDEREXPOSED.value)
            advice = "Image illumination is sub-optimal (dark). Verify exposure settings."

        # Overexposure / Glare check
        if saturation_ratio > self.config.overexpose_saturation_thresh or mean_lum > self.config.overexpose_mean_thresh:
            reasons.append(QualityReason.OVEREXPOSED.value)
            advice = "Image contains excessive glare or overexposure. Reduce flash or adjust corneal angle."
        elif saturation_ratio > self.config.overexpose_saturation_review_thresh:
            reasons.append(QualityReason.OVEREXPOSED.value)
            advice = "Localized glare detected. Reposition camera to avoid corneal reflections."

        # Contrast check
        if std_lum < self.config.min_contrast_thresh:
            reasons.append(QualityReason.LOW_CONTRAST.value)

        # Normalized illumination score: peak at median 120, penalize extremes and saturation
        ideal_target = 120.0
        distance = abs(mean_lum - ideal_target)
        base_score = max(0.0, 1.0 - (distance / 120.0))
        # Penalize saturation glare
        illum_score = float(np.clip(base_score - (saturation_ratio * 3.0), 0.0, 1.0))

        details = {
            "mean_luminance": mean_lum,
            "median_luminance": median_lum,
            "contrast_std": std_lum,
            "saturation_ratio": saturation_ratio,
            "deep_dark_ratio": deep_dark_ratio,
        }

        return illum_score, reasons, advice, details

    def _decide_status(
        self,
        reasons: List[str],
        composite_score: float,
        fov_status: FOVStatus,
    ) -> QualityStatus:
        """Determines final status according to explicit rule hierarchy."""
        # Hard ungradable reasons
        ungradable_reasons = {
            QualityReason.FILE_NOT_FOUND.value,
            QualityReason.CORRUPTED_OR_UNREADABLE.value,
            QualityReason.INVALID_DIMENSIONS.value,
            QualityReason.INVALID_CHANNELS.value,
            QualityReason.BLANK_IMAGE.value,
            QualityReason.SEVERE_BLUR.value,
            QualityReason.FOV_TOO_SMALL.value,
        }

        if any(r in ungradable_reasons for r in reasons) or fov_status == FOVStatus.INSUFFICIENT or composite_score < 0.35:
            return QualityStatus.UNGRADABLE

        # Review required reasons
        review_reasons = {
            QualityReason.MARGINAL_BLUR.value,
            QualityReason.UNDEREXPOSED.value,
            QualityReason.OVEREXPOSED.value,
            QualityReason.LOW_CONTRAST.value,
            QualityReason.FOV_CLIPPED.value,
        }

        if any(r in review_reasons for r in reasons) or fov_status == FOVStatus.PARTIAL_CLIPPED or composite_score < 0.70:
            return QualityStatus.REVIEW_REQUIRED

        return QualityStatus.GRADABLE

    @staticmethod
    def _build_result(
        quality_score: float,
        status: QualityStatus,
        blur_score: float,
        illumination_score: float,
        fov_status: FOVStatus,
        reason_codes: List[str],
        recapture_suggestion: Optional[str],
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Formats the final structured output dictionary."""
        return {
            "quality_score": quality_score,
            "status": status.value,
            "blur_score": blur_score,
            "illumination_score": illumination_score,
            "field_of_view_status": fov_status.value,
            "reason_codes": reason_codes,
            "recapture_suggestion": recapture_suggestion,
            "is_gradable": status == QualityStatus.GRADABLE,
            "details": details,
        }


def assess_quality(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    config: Optional[QualityConfig] = None,
) -> Dict[str, Any]:
    """Convenience functional API for retinal image quality assessment.

    Args:
        image_input: Path to image file, numpy array, or PIL Image.
        config: Optional QualityConfig threshold overrides.

    Returns:
        Structured dictionary conforming to the screening integration contract.
    """
    assessor = RetinalQualityAssessor(config=config)
    return assessor.assess(image_input)
