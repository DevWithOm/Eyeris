"""
Grad-CAM (Gradient-weighted Class Activation Mapping) implementation for Diabetic Retinopathy models.

Grad-CAM highlights the discriminative regions in retinal fundus images that the CNN focused on
when predicting a specific diabetic retinopathy grade.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as transforms

try:
    from ai_models.common.labels import DR_GRADE_LABELS
except ImportError:
    DR_GRADE_LABELS = {
        0: "No DR",
        1: "Mild",
        2: "Moderate",
        3: "Severe",
        4: "Proliferative DR"
    }


def crop_fundus_borders(
    image: Image.Image,
    tol: int = 10
) -> Tuple[Image.Image, Optional[Tuple[int, int, int, int]]]:
    """
    Detects and crops black outer margins from retinal fundus photographs.
    Focuses convolutional neural network receptive fields on diagnostic retinal tissue.
    Matches the logic of Member 1's preprocessing without creating duplicate dependencies.

    Returns:
        Tuple of (cropped_image, crop_box) where crop_box is (xmin, ymin, xmax, ymax)
        or None if no cropping was applied.
    """
    np_img = np.array(image)
    if np_img.ndim == 2:
        mask = np_img > tol
    else:
        mask = np_img.max(axis=2) > tol

    if not np.any(mask):
        return image, None

    row_nonzero = np.where(mask.any(axis=1))[0]
    col_nonzero = np.where(mask.any(axis=0))[0]

    if len(row_nonzero) == 0 or len(col_nonzero) == 0:
        return image, None

    ymin, ymax = int(row_nonzero[0]), int(row_nonzero[-1])
    xmin, xmax = int(col_nonzero[0]), int(col_nonzero[-1])

    # Prevent degenerate crops
    if (ymax - ymin < 50) or (xmax - xmin < 50):
        return image, None

    orig_w, orig_h = image.size
    # If the crop covers virtually the entire image, consider it uncropped
    if xmin <= 0 and ymin <= 0 and xmax >= orig_w - 1 and ymax >= orig_h - 1:
        return image, None

    cropped = image.crop((xmin, ymin, xmax, ymax))
    return cropped, (xmin, ymin, xmax, ymax)


def find_last_conv_layer(model: nn.Module) -> Tuple[str, nn.Module]:
    """
    Safely discovers the last 2D convolutional layer (nn.Conv2d) in any PyTorch model.
    Works dynamically across diverse architectures (e.g. EfficientNet, ResNet, VGG, Custom CNNs)
    without hardcoding layer names.

    Returns:
        Tuple of (layer_name, module_instance)

    Raises:
        ValueError: If no 2D convolutional layer is found in the model.
    """
    last_name = None
    last_module = None

    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            last_name = name
            last_module = module

    if last_module is None:
        raise ValueError(
            "No 2D convolutional layer (nn.Conv2d) could be found in the model. "
            "Please explicitly supply a 'target_layer'."
        )

    return last_name, last_module


def resolve_target_layer(
    model: nn.Module,
    target_layer: Optional[Union[str, nn.Module]] = None
) -> Tuple[str, nn.Module]:
    """
    Resolves the target layer for Grad-CAM inspection.

    If target_layer is None, automatically finds the last convolutional layer.
    If target_layer is a string, looks up the layer by name.
    If target_layer is an nn.Module, validates that it has convolutional or 2D spatial features.
    """
    if target_layer is None:
        return find_last_conv_layer(model)

    if isinstance(target_layer, str):
        named_modules = dict(model.named_modules())
        if target_layer not in named_modules:
            available_convs = [
                name for name, mod in named_modules.items() if isinstance(mod, nn.Conv2d)
            ]
            raise ValueError(
                f"Target layer '{target_layer}' not found in model. "
                f"Available convolutional layers: {available_convs[:10]}..."
            )
        return target_layer, named_modules[target_layer]

    if isinstance(target_layer, nn.Module):
        # Find its name within the model if possible
        for name, mod in model.named_modules():
            if mod is target_layer:
                return name, target_layer
        return target_layer.__class__.__name__, target_layer

    raise TypeError(
        f"target_layer must be None, a layer name (str), or an nn.Module, got {type(target_layer)}"
    )


def get_default_preprocessing(image_size: Tuple[int, int] = (224, 224)) -> transforms.Compose:
    """
    Standard evaluation transform pipeline for retinal fundus images:
    resizes to target dimensions, converts to Tensor, and applies ImageNet normalization.
    """
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def load_retinal_image(
    image_input: Union[str, Path, Image.Image]
) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Safely loads and validates a retinal fundus image from a file path or PIL Image.

    Returns:
        Tuple of (PIL.Image in RGB mode, original (width, height))

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the file is not a valid or readable image.
    """
    if isinstance(image_input, Image.Image):
        img_rgb = image_input.convert("RGB")
        return img_rgb, img_rgb.size

    path = Path(image_input)
    if not path.is_file():
        raise FileNotFoundError(f"Retinal image file not found at: {path.resolve()}")

    try:
        with Image.open(path) as img:
            img_rgb = img.convert("RGB")
            orig_size = img_rgb.size  # (width, height)
            return img_rgb, orig_size
    except Exception as e:
        raise ValueError(f"Failed to read image at '{path}': {e}") from e


def extract_logits_tensor(output: Any) -> torch.Tensor:
    """
    Safely extracts the 2D [batch_size, num_classes] logits tensor from varied model outputs
    (e.g. raw Tensor, dictionary with 'logits' or 'output', or named tuple).
    """
    if isinstance(output, torch.Tensor):
        logits = output
    elif isinstance(output, dict):
        if "logits" in output:
            logits = output["logits"]
        elif "output" in output:
            logits = output["output"]
        else:
            raise ValueError(f"Model output dict missing 'logits' or 'output' key. Keys: {list(output.keys())}")
    elif hasattr(output, "logits"):
        logits = getattr(output, "logits")
    else:
        raise TypeError(f"Unsupported model output type: {type(output)}")

    if logits.ndim == 1:
        logits = logits.unsqueeze(0)

    return logits


def generate_gradcam(
    image_path: Union[str, Path, Image.Image],
    model: nn.Module,
    target_layer: Optional[Union[str, nn.Module]] = None,
    target_class: Optional[int] = None,
    device: Optional[Union[torch.device, str]] = None,
    transform: Optional[Any] = None,
    image_size: Tuple[int, int] = (224, 224),
    crop_borders: bool = False
) -> Dict[str, Any]:
    """
    Generates a Grad-CAM saliency heatmap for a retinal fundus image.

    This function complies with the interface contract:
        generate_gradcam(image_path, model) -> dict

    Args:
        image_path: Path to the input retinal fundus image file, or a PIL Image instance.
        model: A PyTorch classification neural network.
        target_layer: Specific layer name or nn.Module to inspect. If None, the last
                      conv layer is dynamically detected and used.
        target_class: Target DR grade class index (0-4) to explain. If None,
                      the model's top predicted class is used.
        device: Execution device (CPU or CUDA). Defaults to model device or CPU.
        transform: Optional custom image transformation pipeline.
        image_size: Spatial target dimensions (width, height) for inference.
        crop_borders: Whether to detect and crop black fundus margins before model inference.
                      Set to False if image_path is already pre-cropped (avoids double-cropping).

    Returns:
        Dict containing:
            - status: "success"
            - target_class: integer index of the explained class
            - target_class_label: human-readable name of the target class
            - predicted_class: integer index of the model's top predicted class
            - predicted_class_label: human-readable name of the top predicted class
            - confidence: model probability for the top predicted class
            - target_layer: name of the convolutional layer inspected
            - heatmap: 2D numpy.ndarray of shape (H, W) normalized to [0.0, 1.0]
            - original_size: (width, height) of the source image
            - processed_size: (width, height) of the image fed to the network
            - crop_box: (xmin, ymin, xmax, ymax) if cropped, else None
            - original_image: PIL.Image of original input
            - processed_image: PIL.Image after optional border cropping
            - class_probabilities: list of float probabilities across all classes
            - metadata: execution and preprocessing details

    Raises:
        FileNotFoundError: If image_path does not exist.
        ValueError: If image is corrupted, target layer is invalid, or gradients cannot be computed.
    """
    # 1. Load and validate the input retinal image
    pil_image, original_size = load_retinal_image(image_path)

    # 2. Border cropping (avoids double-cropping if already cropped)
    if crop_borders:
        processed_image, crop_box = crop_fundus_borders(pil_image)
    else:
        processed_image = pil_image
        crop_box = None

    # 3. Determine execution device
    if device is None:
        try:
            device = next(model.parameters()).device
        except StopIteration:
            device = torch.device("cpu")
    else:
        device = torch.device(device)

    # 4. Resolve target convolutional layer
    layer_name, target_module = resolve_target_layer(model, target_layer)

    # 5. Preprocess image for model input
    if transform is None:
        transform = get_default_preprocessing(image_size=image_size)

    input_tensor = transform(processed_image).unsqueeze(0).to(device)
    input_tensor.requires_grad_(True)

    # 6. Set up forward and backward hooks with activation cloning for safety
    activations: Optional[torch.Tensor] = None
    gradients: Optional[torch.Tensor] = None

    def forward_hook(_module: nn.Module, _input: Any, output: torch.Tensor) -> None:
        nonlocal activations
        # Clone detached tensor to guard against in-place mutations from subsequent layers
        activations = output.detach().clone()

    def backward_hook(_module: nn.Module, _grad_input: Any, grad_output: Tuple[torch.Tensor, ...]) -> None:
        nonlocal gradients
        if grad_output and grad_output[0] is not None:
            gradients = grad_output[0].detach().clone()

    h_fwd = target_module.register_forward_hook(forward_hook)
    h_bwd = target_module.register_full_backward_hook(backward_hook)

    # Temporarily disable inplace activations to avoid PyTorch BackwardHookFunction view conflicts
    inplace_modules = []
    for mod in model.modules():
        if hasattr(mod, "inplace") and getattr(mod, "inplace", False):
            mod.inplace = False
            inplace_modules.append(mod)

    # 7. Model evaluation and gradient computation
    was_training = model.training
    model.eval()

    try:
        # Enable gradients explicitly so Grad-CAM functions even if caller invoked under torch.no_grad()
        with torch.set_grad_enabled(True):
            model.zero_grad(set_to_none=True)
            raw_output = model(input_tensor)
            logits = extract_logits_tensor(raw_output)

            probs = torch.softmax(logits, dim=-1)
            pred_class = int(torch.argmax(logits, dim=-1).item())
            confidence = float(probs[0, pred_class].item())

            if target_class is None:
                chosen_class = pred_class
            else:
                chosen_class = int(target_class)
                num_classes = logits.shape[-1]
                if not (0 <= chosen_class < num_classes):
                    raise ValueError(
                        f"Target class {chosen_class} is out of bounds for model with {num_classes} classes."
                    )

            # Target class score
            score = logits[0, chosen_class]
            score.backward(retain_graph=False)

        # 8. Validate captured activations and gradients
        if activations is None:
            raise RuntimeError(f"Forward hook failed to capture activations on layer '{layer_name}'.")
        if gradients is None:
            raise RuntimeError(
                f"Backward hook failed to capture gradients on layer '{layer_name}'. "
                "Ensure the model allows gradient propagation from output to this layer."
            )

        if activations.ndim != 4 or gradients.ndim != 4:
            raise ValueError(
                f"Expected 4D activations [B, C, H, W] from convolutional layer, "
                f"got activation shape {list(activations.shape)}."
            )

        # 9. Compute Grad-CAM weights and map
        # Global average pooling of gradients: alpha_k = (1 / Z) * sum(gradients)
        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)  # Shape: [1, C, 1, 1]

        # Linear combination: L_GradCAM = ReLU( sum(alpha_k * activations) )
        cam = torch.sum(weights * activations, dim=1)  # Shape: [1, H, W]
        cam = torch.relu(cam)

        cam_np = cam[0].cpu().numpy().astype(np.float32)

        # 10. Normalize heatmap to [0.0, 1.0]
        cam_min = float(np.min(cam_np))
        cam_max = float(np.max(cam_np))

        if (cam_max - cam_min) > 1e-8:
            normalized_heatmap = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            # Handle uniform activation or zero gradient gracefully
            normalized_heatmap = np.zeros_like(cam_np, dtype=np.float32)

        class_probs = probs[0].detach().cpu().numpy().tolist()

        return {
            "status": "success",
            "target_class": chosen_class,
            "target_class_label": DR_GRADE_LABELS.get(chosen_class, f"Grade {chosen_class}"),
            "predicted_class": pred_class,
            "predicted_class_label": DR_GRADE_LABELS.get(pred_class, f"Grade {pred_class}"),
            "confidence": confidence,
            "target_layer": layer_name,
            "heatmap": normalized_heatmap,
            "original_size": original_size,
            "processed_size": processed_image.size,
            "crop_box": crop_box,
            "original_image": pil_image,
            "processed_image": processed_image,
            "class_probabilities": class_probs,
            "metadata": {
                "method": "Grad-CAM",
                "image_path": str(Path(image_path).resolve()) if isinstance(image_path, (str, Path)) else "PIL.Image",
                "image_size": list(image_size),
                "device": str(device),
                "crop_borders": crop_borders
            }
        }

    finally:
        # Always remove hooks, restore inplace states, and clear parameter gradients
        h_fwd.remove()
        h_bwd.remove()
        for mod in inplace_modules:
            mod.inplace = True
        model.zero_grad(set_to_none=True)
        model.train(was_training)
