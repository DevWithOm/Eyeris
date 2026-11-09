# Diabetic Retinopathy Classification Project

Starter folder structure for Member 1's DR classification work.

## Where to put datasets

### APTOS 2019 (primary training dataset)
- Put extracted training images in `data/raw/aptos/train_images/`
- Put the APTOS `train.csv` in `data/raw/aptos/train.csv`
- Common CSV columns are `id_code` and `diagnosis`, but inspect the actual CSV before assuming.

### IDRiD (external evaluation)
- Extract `B. Disease Grading.zip` into `data/raw/idrid/disease_grading/`
- Keep image folders and grading-label files in their original structure.
- Do not rename files until the folder structure and label mapping have been inspected.

## Folder guide
- `src/`: reusable Python modules
- `scripts/`: runnable scripts
- `notebooks/`: exploration and training notebooks
- `configs/`: configuration
- `data/splits/`: train/validation/test manifests
- `data/processed/`: optional processed data
- `outputs/plots/`: charts and confusion matrices
- `outputs/reports/`: metric reports
- `checkpoints/`: saved model weights

## Evaluation rules
- Train primarily on APTOS.
- Create stratified train/validation/test splits and keep the test split locked until final evaluation.
- Evaluate IDRiD separately, only if compatible grading labels are available.
- Never fabricate metrics; report only results actually produced by running code.
- Avoid committing datasets and large model weights to public source control.

## Next step
Open this whole folder in Antigravity and ask it to inspect the data, implement the pipeline, run it, fix errors, and report what actually executed.
