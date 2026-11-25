"""
Diabetic Retinopathy Classification Module (Member 1).

Exposes model loading, inference preprocessing, prediction, and evaluation routines
for 5-class diabetic retinopathy severity grading.
"""

from ai_models.classification.evaluate import run_test_evaluation
from ai_models.classification.model import (
    DEFAULT_CHECKPOINT_PATH,
    build_efficientnet_b0,
    get_classification_model,
    get_gradcam_target_layer,
)
from ai_models.classification.predict import (
    MODEL_NAME,
    MODEL_VERSION,
    get_cached_model,
    predict_grade,
)
from ai_models.classification.preprocessing import (
    crop_fundus_borders,
    get_inference_transforms,
    preprocess_fundus_image,
)

__all__ = [
    "predict_grade",
    "get_classification_model",
    "get_cached_model",
    "get_gradcam_target_layer",
    "build_efficientnet_b0",
    "preprocess_fundus_image",
    "crop_fundus_borders",
    "get_inference_transforms",
    "run_test_evaluation",
    "DEFAULT_CHECKPOINT_PATH",
    "MODEL_NAME",
    "MODEL_VERSION",
]
