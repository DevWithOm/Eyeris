"""
Unit and module tests for Grad-CAM explainability and visualization helpers.
"""

from pathlib import Path
import shutil
import tempfile
import unittest
import numpy as np
from PIL import Image
import torch
import torch.nn as nn

from ai_models.explainability.gradcam import (
    crop_fundus_borders,
    find_last_conv_layer,
    generate_gradcam,
    resolve_target_layer
)
from ai_models.explainability.visualization import (
    colorize_heatmap,
    overlay_heatmap_on_image,
    project_heatmap_to_original,
    save_explanation_artifacts
)


class DummyRetinaCNN(nn.Module):
    """
    A lightweight CNN for testing Grad-CAM without external weights or downloads.
    """
    def __init__(self, num_classes: int = 5):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 8, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),  # Test with inplace=True to verify activation clone safety
            nn.AdaptiveAvgPool2d((4, 4))
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(16 * 4 * 4, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


class TestGradCAM(unittest.TestCase):
    def setUp(self):
        # Create temporary working directory for test artifacts and images
        self.test_dir = tempfile.mkdtemp()
        self.img_width, self.img_height = 120, 100

        # Create a synthetic fundus image with black outer borders
        # Canvas: 100 high x 120 wide, with 10px black margin on all sides
        img_array = np.zeros((self.img_height, self.img_width, 3), dtype=np.uint8)
        # Retinal tissue inside [10:90, 10:110]
        img_array[10:90, 10:110, 0] = 180  # R
        img_array[10:90, 10:110, 1] = 70   # G
        img_array[10:90, 10:110, 2] = 30   # B
        # Optic disc artifact
        yy, xx = np.ogrid[10:90, 10:110]
        center_mask = ((xx - 60)**2 + (yy - 50)**2) < 15**2
        img_array[10:90, 10:110][center_mask] = [240, 220, 100]

        self.test_image_path = Path(self.test_dir) / "test_retina.png"
        Image.fromarray(img_array).save(self.test_image_path)

        # Initialize test model
        torch.manual_seed(42)
        self.model = DummyRetinaCNN(num_classes=5)
        self.model.eval()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_find_last_conv_layer(self):
        layer_name, layer_module = find_last_conv_layer(self.model)
        self.assertEqual(layer_name, "features.2")
        self.assertIsInstance(layer_module, nn.Conv2d)

    def test_resolve_target_layer_explicit(self):
        name, mod = resolve_target_layer(self.model, "features.0")
        self.assertEqual(name, "features.0")
        self.assertIsInstance(mod, nn.Conv2d)

    def test_resolve_target_layer_invalid_name(self):
        with self.assertRaises(ValueError):
            resolve_target_layer(self.model, "non_existent_conv_layer")

    def test_generate_gradcam_success(self):
        result = generate_gradcam(
            image_path=self.test_image_path,
            model=self.model,
            image_size=(64, 64)
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("target_class", result)
        self.assertIn("target_class_label", result)
        self.assertIn("predicted_class", result)
        self.assertIn("confidence", result)
        self.assertEqual(result["target_layer"], "features.2")
        self.assertEqual(result["original_size"], (self.img_width, self.img_height))
        self.assertEqual(result["processed_size"], (self.img_width, self.img_height))
        self.assertIsNone(result["crop_box"])

        # Check heatmap properties
        heatmap = result["heatmap"]
        self.assertIsInstance(heatmap, np.ndarray)
        self.assertEqual(heatmap.ndim, 2)
        self.assertGreaterEqual(float(np.min(heatmap)), 0.0)
        self.assertLessEqual(float(np.max(heatmap)), 1.0)

        # Probabilities
        probs = result["class_probabilities"]
        self.assertEqual(len(probs), 5)
        self.assertAlmostEqual(sum(probs), 1.0, places=4)

    def test_generate_gradcam_inside_torch_no_grad(self):
        """
        Verify that Grad-CAM computes gradients and succeeds even when called
        inside an active `torch.no_grad()` context.
        """
        with torch.no_grad():
            self.assertFalse(torch.is_grad_enabled())
            result = generate_gradcam(
                image_path=self.test_image_path,
                model=self.model,
                image_size=(64, 64)
            )
            # Should still be disabled outside
            self.assertFalse(torch.is_grad_enabled())

        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["heatmap"], np.ndarray)
        self.assertGreaterEqual(float(np.max(result["heatmap"])), 0.0)

    def test_generate_gradcam_clears_parameter_gradients(self):
        """
        Verify that residual parameter gradients on the model weights are cleared (set to None)
        in the finally block after execution.
        """
        _ = generate_gradcam(
            image_path=self.test_image_path,
            model=self.model,
            image_size=(64, 64)
        )

        for param in self.model.parameters():
            self.assertIsNone(param.grad, "Model parameters should have None .grad after execution")

    def test_generate_gradcam_with_border_cropping(self):
        """
        Verify that border cropping crops black margins, returns crop_box,
        and produces matching spatial outputs.
        """
        result = generate_gradcam(
            image_path=self.test_image_path,
            model=self.model,
            image_size=(64, 64),
            crop_borders=True
        )

        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["crop_box"])
        xmin, ymin, xmax, ymax = result["crop_box"]

        # Original is 120x100, border was 10px on each side
        self.assertEqual(result["original_size"], (120, 100))
        self.assertLess(result["processed_size"][0], 120)
        self.assertLess(result["processed_size"][1], 100)
        self.assertEqual(result["processed_size"], (xmax - xmin, ymax - ymin))

        # Test avoiding double-cropping: passing pre-cropped image with crop_borders=False
        cropped_img = result["processed_image"]
        result2 = generate_gradcam(
            image_path=cropped_img,
            model=self.model,
            image_size=(64, 64),
            crop_borders=False
        )
        self.assertIsNone(result2["crop_box"])
        self.assertEqual(result2["processed_size"], cropped_img.size)

    def test_project_heatmap_to_original_coordinates(self):
        """
        Verify projecting a cropped region heatmap back onto the full original coordinates.
        """
        original_size = (120, 100)
        crop_box = (10, 10, 110, 90)  # w=100, h=80
        crop_heatmap = np.ones((8, 10), dtype=np.float32)

        full_heatmap = project_heatmap_to_original(crop_heatmap, original_size, crop_box)

        # Full heatmap shape is (H, W) -> (100, 120)
        self.assertEqual(full_heatmap.shape, (100, 120))
        # Borders (0:10, 0:10) should be 0.0
        self.assertEqual(full_heatmap[0, 0], 0.0)
        self.assertEqual(full_heatmap[99, 119], 0.0)
        # Inside the crop box should be positive
        self.assertGreater(full_heatmap[50, 60], 0.0)

    def test_generate_gradcam_specific_target_class(self):
        result = generate_gradcam(
            image_path=self.test_image_path,
            model=self.model,
            target_class=3,
            image_size=(64, 64)
        )
        self.assertEqual(result["target_class"], 3)
        self.assertEqual(result["target_class_label"], "Severe")

    def test_generate_gradcam_removes_hooks_cleanly(self):
        # Verify no hooks registered initially
        for mod in self.model.modules():
            self.assertEqual(len(mod._forward_hooks), 0)
            self.assertEqual(len(mod._backward_hooks), 0)

        _ = generate_gradcam(self.test_image_path, self.model, image_size=(64, 64))

        # Verify all hooks were removed after execution
        for mod in self.model.modules():
            self.assertEqual(len(mod._forward_hooks), 0)
            self.assertEqual(len(mod._backward_hooks), 0)

    def test_generate_gradcam_missing_image_file(self):
        non_existent = Path(self.test_dir) / "does_not_exist.png"
        with self.assertRaises(FileNotFoundError):
            generate_gradcam(non_existent, self.model)

    def test_overlay_heatmap_on_image(self):
        # 10x10 synthetic heatmap
        heatmap = np.linspace(0.0, 1.0, 100).reshape((10, 10)).astype(np.float32)

        orig_pil, heatmap_colored, overlay = overlay_heatmap_on_image(
            image=self.test_image_path,
            heatmap=heatmap,
            alpha=0.4,
            colormap_name="jet"
        )

        # Verify that all output images retain the exact original resolution
        self.assertEqual(orig_pil.size, (self.img_width, self.img_height))
        self.assertEqual(heatmap_colored.size, (self.img_width, self.img_height))
        self.assertEqual(overlay.size, (self.img_width, self.img_height))

        # Verify invalid alpha raises ValueError
        with self.assertRaises(ValueError):
            overlay_heatmap_on_image(self.test_image_path, heatmap, alpha=1.5)

    def test_save_explanation_artifacts(self):
        heatmap = np.zeros((10, 10), dtype=np.float32)
        orig, hm, ov = overlay_heatmap_on_image(self.test_image_path, heatmap)

        saved = save_explanation_artifacts(
            output_dir=self.test_dir,
            prefix="test_screening",
            original=orig,
            heatmap_colored=hm,
            overlay=ov,
            heatmap_raw=heatmap
        )

        self.assertTrue(Path(saved["original"]).is_file())
        self.assertTrue(Path(saved["heatmap"]).is_file())
        self.assertTrue(Path(saved["overlay"]).is_file())
        self.assertTrue(Path(saved["raw_npy"]).is_file())


if __name__ == "__main__":
    unittest.main()
