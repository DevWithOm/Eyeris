"""
Inference and clinical prediction helper for Diabetic Retinopathy fundus images.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
from PIL import Image
import torch
import torch.nn as nn

from src.data import crop_fundus_borders, get_transforms

CLASS_NAMES_DEFAULT = [
    "0 - No DR",
    "1 - Mild",
    "2 - Moderate",
    "3 - Severe",
    "4 - Proliferative DR"
]


def predict_retinopathy(
    image_input: Union[str, Path, Image.Image, np.ndarray],
    model: nn.Module,
    device: torch.device,
    transform: Optional[object] = None,
    crop_borders: bool = True,
    class_names: Optional[List[str]] = None,
    referable_threshold: int = 2,
    image_size: int = 224
) -> Dict:
    """
    Performs inference on a single retinal fundus image.
    Outputs:
      - Predicted DR grade (0 to 4)
      - Class label string
      - Prediction confidence percentage
      - Full class probability array
      - Binary Referable DR status and clinical recommendation text
    """
    if class_names is None:
        class_names = CLASS_NAMES_DEFAULT

    # Load / convert PIL image
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, np.ndarray):
        img = Image.fromarray(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    if crop_borders:
        cropped = crop_fundus_borders(img)
    else:
        cropped = img

    if transform is None:
        transform = get_transforms(image_size=image_size, is_training=False)

    tensor = transform(cropped).unsqueeze(0).to(device)

    model.eval()
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        pred_grade = int(np.argmax(probs))
        confidence = float(probs[pred_grade])

    is_referable = (pred_grade >= referable_threshold)
    referral_text = (
        "REFERRAL REQUIRED (Grades 2-4: Referable Diabetic Retinopathy)"
        if is_referable
        else "Non-Referable / Routine Annual Screening (Grades 0-1)"
    )

    return {
        "predicted_grade": pred_grade,
        "class_name": class_names[pred_grade],
        "confidence": confidence,
        "is_referable": is_referable,
        "referral_recommendation": referral_text,
        "class_probabilities": probs.tolist(),
        "original_image": img,
        "cropped_image": cropped
    }
