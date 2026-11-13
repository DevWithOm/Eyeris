# Integration Contract

Proposed entry point: `integration.pipeline.analyse_case(image_path, config) -> dict`.

Module interfaces:
- `assess_quality(image_path) -> dict`
- `predict_grade(image_path) -> dict`
- `segment_lesions(image_path) -> dict`
- `generate_gradcam(image_path, model) -> dict`

Freeze field names, types, preprocessing, model versions and error codes before parallel implementation. Distinguish raw probability, calibrated confidence and clinical decision. Example values in design discussions are schemas only, not model results.
