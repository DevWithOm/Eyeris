"""
Reproducible data preparation, verification, and lightweight pipeline sanity check.
Generates locked split manifests in data/splits/ without modifying original data.
Performs integrity checks and runs a 1-batch dry-run forward pass.
"""

import os
from pathlib import Path
import sys
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import torch

from src.data import (
    compute_class_weights,
    create_stratified_splits,
    get_dataloaders,
    validate_aptos_dataset,
    validate_idrid_dataset
)
from src.model import build_efficientnet_b0, get_loss_criterion
from src.evaluate import compute_comprehensive_metrics


def run_pipeline_preparation():
    print("=" * 75)
    print("🚀 DIABETIC RETINOPATHY PIPELINE PREPARATION & VERIFICATION")
    print("=" * 75)

    # 1. Load Configuration
    config_path = ROOT / "configs" / "default.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    print(f"Loaded configuration from: {config_path}")
    print(f"Seed: {config['seed']}, Target image size: {config['image_size']}x{config['image_size']}")

    # 2. Inspect & Validate APTOS Dataset
    print("\n" + "-" * 75)
    print("1. VALIDATING APTOS TRAINING DATASET")
    print("-" * 75)

    aptos_csv = ROOT / config["paths"]["aptos_csv"]
    aptos_img_dir = ROOT / config["paths"]["aptos_images"]

    df_aptos, aptos_report = validate_aptos_dataset(aptos_csv, aptos_img_dir)
    print(f"✅ APTOS validation successful:")
    print(f"   • Total verified records: {aptos_report['valid_rows']}")
    print(f"   • Duplicate image IDs   : {aptos_report['duplicate_ids']}")
    print(f"   • Missing labels in CSV : {aptos_report['missing_labels']}")
    print(f"   • Missing images on disk: {aptos_report['missing_images_on_disk']}")
    print(f"   • Unique class values   : {aptos_report['unique_classes']}")
    print(f"   • Class distribution    : {aptos_report['class_distribution']}")

    # 3. Inspect & Validate IDRiD Datasets
    print("\n" + "-" * 75)
    print("2. VALIDATING IDRiD DATASETS (GROUNDTRUTHS & IMAGES)")
    print("-" * 75)

    idrid_train_csv = ROOT / config["paths"]["idrid_train_csv"]
    idrid_train_img_dir = ROOT / config["paths"]["idrid_train_images"]
    df_idrid_train, idrid_train_report = validate_idrid_dataset(
        idrid_train_csv, idrid_train_img_dir, is_test_set=False
    )
    print(f"✅ IDRiD Training Set validation successful:")
    print(f"   • Identified Image ID col  : '{idrid_train_report['identified_id_col']}'")
    print(f"   • Identified DR Grade col  : '{idrid_train_report['identified_grade_col']}'")
    print(f"   • Unnamed columns excluded : {idrid_train_report['unnamed_cols_excluded']}")
    print(f"   • Unnamed status check     : All confirmed empty artifacts (100% null or single space)")
    print(f"   • Ignored columns          : {idrid_train_report['ignored_columns']} (e.g. macular edema)")
    print(f"   • Total verified records   : {idrid_train_report['valid_rows']}")
    print(f"   • Missing images on disk   : {idrid_train_report['missing_images_on_disk']}")
    print(f"   • Class distribution       : {idrid_train_report['class_distribution']}")

    idrid_test_csv = ROOT / config["paths"]["idrid_test_csv"]
    idrid_test_img_dir = ROOT / config["paths"]["idrid_test_images"]
    df_idrid_test, idrid_test_report = validate_idrid_dataset(
        idrid_test_csv, idrid_test_img_dir, is_test_set=True
    )
    print(f"\n✅ IDRiD Testing Set (External Evaluation) validation successful:")
    print(f"   • Identified Image ID col  : '{idrid_test_report['identified_id_col']}'")
    print(f"   • Identified DR Grade col  : '{idrid_test_report['identified_grade_col']}'")
    print(f"   • Total verified records   : {idrid_test_report['valid_rows']} (Reserved for external test)")
    print(f"   • Missing images on disk   : {idrid_test_report['missing_images_on_disk']}")
    print(f"   • Class distribution       : {idrid_test_report['class_distribution']}")

    # 4. Generate Stratified Splits
    print("\n" + "-" * 75)
    print("3. GENERATING REPRODUCIBLE STRATIFIED APTOS SPLITS (70 / 15 / 15)")
    print("-" * 75)

    splits_dir = ROOT / config["paths"]["splits_dir"]
    train_ratio = config["split_ratios"]["train"]
    val_ratio = config["split_ratios"]["val"]
    test_ratio = config["split_ratios"]["test"]

    df_train, df_val, df_test = create_stratified_splits(
        df_aptos,
        target_ratios=(train_ratio, val_ratio, test_ratio),
        seed=config["seed"],
        label_col="diagnosis",
        id_col="id_code",
        output_dir=splits_dir
    )

    print(f"✅ Stratified splits successfully saved to: {splits_dir}")
    print(f"   • Train split : {len(df_train)} images ({len(df_train)/len(df_aptos)*100:.2f}%)")
    print(f"   • Val split   : {len(df_val)} images ({len(df_val)/len(df_aptos)*100:.2f}%)")
    print(f"   • Test split  : {len(df_test)} images ({len(df_test)/len(df_aptos)*100:.2f}%) [LOCKED]")

    # Check split overlap
    set_train = set(df_train["id_code"])
    set_val = set(df_val["id_code"])
    set_test = set(df_test["id_code"])

    assert len(set_train & set_val) == 0, "Train & Val overlap detected!"
    assert len(set_train & set_test) == 0, "Train & Test overlap detected!"
    assert len(set_val & set_test) == 0, "Val & Test overlap detected!"
    print("✅ Verified 0 identifier overlap across all 3 splits.")

    # Display stratification table
    strat_df = pd.DataFrame({
        "Grade": range(5),
        "Name": config["class_names_short"],
        "Train_Count": df_train["diagnosis"].value_counts().sort_index().values,
        "Train_%": (df_train["diagnosis"].value_counts().sort_index().values / len(df_train) * 100).round(2),
        "Val_Count": df_val["diagnosis"].value_counts().sort_index().values,
        "Val_%": (df_val["diagnosis"].value_counts().sort_index().values / len(df_val) * 100).round(2),
        "Test_Count": df_test["diagnosis"].value_counts().sort_index().values,
        "Test_%": (df_test["diagnosis"].value_counts().sort_index().values / len(df_test) * 100).round(2),
    })
    print("\nStratification Verification Table:")
    print(strat_df.to_string(index=False))

    # 5. Class Weights for Handling Severe Imbalance
    print("\n" + "-" * 75)
    print("4. CLASS IMBALANCE HANDLING (BALANCED WEIGHTS)")
    print("-" * 75)

    class_weights = compute_class_weights(df_train, label_col="diagnosis", num_classes=5)
    print(f"Computed normalized class weights for CrossEntropyLoss:")
    for grade_idx, w in enumerate(class_weights.tolist()):
        print(f"   • Grade {grade_idx} ({config['class_names_short'][grade_idx]}): {w:.4f}")

    # 6. DataLoaders and 1-Batch Dry-Run Forward Pass
    print("\n" + "-" * 75)
    print("5. LIGHTWEIGHT PIPELINE INTEGRATION CHECK (1-BATCH DRY RUN)")
    print("-" * 75)

    train_loader, val_loader, test_loader = get_dataloaders(
        df_train,
        df_val,
        df_test,
        img_dir=aptos_img_dir,
        batch_size=4,  # Small batch for dry-run
        num_workers=0,
        image_size=config["image_size"],
        crop_borders=config["crop_borders"]
    )

    sample_images, sample_labels, sample_ids = next(iter(train_loader))
    print(f"✅ DataLoader batch successfully sampled:")
    print(f"   • Batch images shape : {sample_images.shape} (Batch, Channel, Height, Width)")
    print(f"   • Batch labels shape : {sample_labels.shape}")
    print(f"   • Sample image IDs   : {list(sample_ids)}")
    print(f"   • Sample labels      : {sample_labels.tolist()}")

    # Model instantiation
    print("\nInstantiating EfficientNet-B0 architecture (5-class output)...")
    model = build_efficientnet_b0(num_classes=5, pretrained=True, dropout=0.3)
    model.eval()

    with torch.no_grad():
        logits = model(sample_images)
        probs = torch.softmax(logits, dim=1)
        preds = torch.argmax(probs, dim=1)

    print(f"✅ Forward pass completed successfully:")
    print(f"   • Output logits shape : {logits.shape}")
    print(f"   • Output probabilities:\n{probs.numpy().round(4)}")
    print(f"   • Predicted classes   : {preds.tolist()}")

    # Test Loss computation
    criterion = get_loss_criterion(class_weights=class_weights)
    loss = criterion(logits, sample_labels)
    print(f"   • Dry-run loss value  : {loss.item():.4f}")

    # Test Metric computation function
    dummy_true = [0, 1, 2, 3, 4]
    dummy_pred = [0, 1, 2, 2, 4]
    dummy_metrics = compute_comprehensive_metrics(dummy_true, dummy_pred, referable_threshold=2)
    print(f"✅ Comprehensive metrics computation test:")
    print(f"   • Overall Accuracy        : {dummy_metrics['overall_accuracy']:.2f}")
    print(f"   • Macro F1 Score          : {dummy_metrics['macro_f1']:.4f}")
    print(f"   • Referable Sensitivity   : {dummy_metrics['referable_dr']['sensitivity'] * 100:.1f}%")
    print(f"   • Referable Specificity   : {dummy_metrics['referable_dr']['specificity'] * 100:.1f}%")

    print("\n" + "=" * 75)
    print("🎉 ALL PREPARATION CHECKS PASSED WITH ZERO ERRORS!")
    print("   Data splits are locked. Pipeline components are verified and ready for Colab.")
    print("=" * 75)


if __name__ == "__main__":
    run_pipeline_preparation()
