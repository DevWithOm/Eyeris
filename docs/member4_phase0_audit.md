# EYERIS — Phase 0 Repository Audit Report
**Role**: Senior Software Architect, Technical Lead & Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System  
**Problem Statement**: SIH PS26038  
**Date**: November 2026  
**Status**: Completed  

---

## 1. Executive Summary

This report establishes the baseline technical audit for the **EYERIS** diabetic retinopathy screening repository prior to the commencement of implementation. The repository was audited across all subsystems: backend (FastAPI), frontend (React + Vite), machine learning modules (`ai_models/`), computer vision modules (`computer_vision/`), integration orchestrator (`integration/`), MATLAB and Simulink scaffolding (`matlab/`, `simulink/`), Docker configuration, dependencies, test suites, and remote Git branch states.

### Key Audit Findings
1. **Repository Structure**: The project root contains a clean, modular directory scaffold designed as a modular monolith.
2. **Current Branch & Git State**: The current working branch is `om` (tracking `origin/om`). The prompt specification designates `integration/member-4`. The working tree is clean with zero uncommitted changes.
3. **Cross-Branch Audit & Divergence Risk**:
   - `origin/Shourya-Thorat` (Member 1 — Classifier): Branched from root commit `cf024bc` before the modular scaffold commit `dea8a27`. It implemented classification inside a standalone `src/` directory and Colab notebook, deleting scaffold directories. Merging directly would result in catastrophic structural collisions.
   - `origin/Sanmit-Patil` (Member 2 — Quality & Segmentation): Branched from `05f62f6` (scaffold preserved). Implemented quality checks and segmentation under `src/vision/` while adding hooks into `ai_models/segmentation/` and comprehensive documentation.
   - `origin/Siddhi-Garg` (Member 3 — Explainability): Branched from `05f62f6` (scaffold preserved). Adhered strictly to the scaffold layout under `ai_models/explainability/` with temperature scaling and Grad-CAM implementations and test suites.
4. **Backend State**: Scaffold complete with working `GET /api/health` and basic SQLAlchemy model `ScreeningRecord`. Database session engine instantiates synchronously upon module import. Schemas and services are stubbed out.
5. **Frontend State**: React 18 + Vite scaffold with React Router DOM configured for `/` and `/screening`. Component subdirectories exist with `.gitkeep`. `npm install` has not been executed; `node_modules` is not yet populated.
6. **MATLAB & Simulink State**: Placeholder scripts and READMEs present. No binary `.slx` model exists. MATLAB executable and SimEvents toolbox are not installed on the host environment.
7. **Docker Configuration**: `Dockerfile` installs only `requirements-backend.txt`, but copies `integration/`, `ai_models/`, and `computer_vision/`. Without ML dependencies (`requirements-ml.txt`), running the full pipeline in Docker will trigger `ModuleNotFoundError`.
8. **Test Execution**: Unit smoke test passes in 0.45s (`pytest tests/unit/test_project_smoke.py`). Health check test passes in 1.05s (`pytest backend/tests/test_health.py`). End-to-end test is marked skipped pending pipeline implementation. Scaffold validation script (`scripts/validate_project.py`) passes.

---

## 2. Comprehensive Inventory of Repository Components

| Directory / Subsystem | Intended Responsibility | Existing Files | Functional Status | Audit Assessment |
| :--- | :--- | :--- | :--- | :--- |
| `ai_models/classification/` | EfficientNet-B0 DR grading (0–4) | `__init__.py`, `evaluate.py`, `model.py`, `model_config.yaml`, `predict.py`, `preprocessing.py`, `train.py` | Stubs (`predict_grade` raises `NotImplementedError`) | Skeleton only on `main`/`om`. Member 1 developed code on `origin/Shourya-Thorat` under `src/`. Needs adapter pattern. |
| `ai_models/common/` | Shared ML transforms, label mappings, weights loader | `__init__.py`, `labels.py`, `model_loader.py`, `transforms.py`, `utils.py` | `labels.py` defines `DR_GRADE_LABELS`. Others are stubs. | Functional label dictionary. Loader and transforms need implementation. |
| `ai_models/explainability/` | Grad-CAM, calibration, uncertainty estimation | `__init__.py`, `calibration.py`, `confidence.py`, `evaluate_explanations.py`, `gradcam.py`, `visualization.py` | Stubs on `main`/`om`. Member 3 implemented calibration and Grad-CAM on `origin/Siddhi-Garg`. | Adheres strictly to scaffold paths on Member 3 branch. Ready for review. |
| `ai_models/segmentation/` | Retinal lesion segmentation (U-Net) | `__init__.py`, `evaluate.py`, `model_config.yaml`, `predict.py`, `train.py`, `unet.py` | Stubs on `main`/`om`. Member 2 implemented segmentation on `origin/Sanmit-Patil` under `src/vision/segmentation/` and `ai_models/segmentation/dataset.py`. | Functional on feature branch. Needs canonical adapter alignment. |
| `artifacts/` | Model registry and serialized artifacts | `model_registry/.gitkeep` | Empty directory | Awaiting trained model weights and validation artifacts. |
| `backend/app/` | FastAPI REST API application | `main.py`, `api/`, `core/`, `db/`, `schemas/`, `services/`, `utils/` | `main.py` and `api/routes/health.py` functional. Schemas and services are stub files. | Clean architecture. Needs endpoint definitions and service layer implementation. |
| `computer_vision/` | Traditional CV: Quality assessment, preprocessing, lesion filters | `__init__.py`, `common/`, `image_quality/`, `lesion_analysis/`, `preprocessing/` | Empty `__init__.py` files on `main`/`om`. Member 2 implemented quality in `src/vision/quality.py`. | Needs integration wrapper into `computer_vision/image_quality/`. |
| `config/` | Application, database, decision, and model configs | `baseline.yaml`, `database.yaml`, `decision_policy.yaml`, `model_config.yaml` | Functional YAML files with initial structures. | Thresholds are deliberately uncalibrated (`null`). Configuration loader required. |
| `data/` | Dataset manifests and mounts | `manifests/.gitkeep` | Empty directory | Complies with rule: no raw clinical images committed. |
| `docs/` | Architecture and governance documentation | 9 Markdown documents | Functional reference documents. | All documents are brief; require technical depth and formalization. |
| `frontend/` | React 18 + Vite User Interface | `App.jsx`, `main.jsx`, `api.js`, `global.css`, `package.json`, `vite.config.js` | Basic router functional with two placeholder routes. Subdirectories contain `.gitkeep`. | Clean starting point. Needs screening upload, results visualization, and report UI. |
| `integration/` | End-to-end pipeline, decision engine, report generation | `pipeline.py`, `decision_engine.py`, `model_orchestrator.py`, `report_generator.py`, `result_formatter.py`, `error_handler.py` | Stubs (`analyse_case` raises `NotImplementedError`). | Core ownership of Member 4. Foundation for multi-module orchestration. |
| `matlab/` | MATLAB App Designer and Python bridge | `README.md`, `api_connector.m`, `data_exchange.m`, `python_bridge.m` | Functions raise `NotImplementedError` or return placeholders. | Stubs in place. Host environment lacks MATLAB. |
| `simulink/` | Clinic screening workflow simulation | `README.md`, `high_volume_scenario.m`, `normal_workflow.m`, `poor_quality_scenario.m`, `run_simulation.m` | Stubs. No binary `.slx` model exists. | Stubs in place. Host environment lacks Simulink / SimEvents. |
| `scripts/` | Project verification and helper scripts | `validate_project.py`, `setup_environment.py`, `run_backend.py`, `initialize_database.py`, `run_frontend.sh` | `validate_project.py` and `setup_environment.py` are functional. | High utility for automated validation. |
| `tests/` | Unit, integration, model, and E2E test suites | `test_project_smoke.py`, `test_complete_screening.py`, `test_health.py` | Smoke and health tests pass. E2E is skipped. | Valid test runner setup (`pytest.ini`). |

---

## 3. Subsystem Audit Details

### 3.1 Backend Architecture
- **Framework**: FastAPI `>=0.110,<1` with Pydantic settings.
- **Entrypoint**: `backend/app/main.py` binds CORS for `http://localhost:5173`, registers `/api/health`, and serves `/` root info.
- **Database & ORM**: SQLAlchemy 2.0 with PostgreSQL driver `psycopg` (binary 3.1). `backend/app/db/session.py` creates an engine via `create_engine(settings.database_url, pool_pre_ping=True)`.
  *Audit Observation*: Instantiating `engine` at module level will attempt database connectivity if pool pre-ping or table reflection is triggered, and will fail if PostgreSQL is offline. Lazy session initialization or health probe decoupling is advised.
- **Alembic**: `alembic.ini` and `backend/migrations/env.py` exist, but `migrations/versions/` contains only `.gitkeep`. No schema migrations have been generated yet.
- **Schemas & Services**: All files in `backend/app/schemas/` and `backend/app/services/` are single-line comments.

### 3.2 Frontend Architecture
- **Framework**: React 18.3.1 with Vite 5.4.8 and React Router DOM 6.26.2.
- **Entrypoint**: `frontend/src/main.jsx` mounts `BrowserRouter` and renders `App.jsx`.
- **API Client**: `frontend/src/services/api.js` defines an `apiRequest` wrapper over native `fetch` targeting `VITE_API_BASE_URL` or `http://localhost:8000/api`.
- **Styling**: `frontend/src/styles/global.css` has basic reset and `.container` styling.
- **State & Packages**: No state library (e.g. Zustand, Redux) is installed; React built-in state/context is sufficient for this scope. `node_modules` is currently absent.

### 3.3 AI Models & Computer Vision
- **Classification (`ai_models/classification/`)**:
  - `DR_GRADE_LABELS` in `ai_models/common/labels.py` maps `{0: "No DR", 1: "Mild", 2: "Moderate", 3: "Severe", 4: "Proliferative DR"}`.
  - On `main`/`om`, `predict_grade` is stubbed.
  - Member 1's branch (`origin/Shourya-Thorat`) contains `src/model.py` (EfficientNet-B0 with custom classifier head), `src/data.py`, and `src/predict.py`.
- **Segmentation (`ai_models/segmentation/`)**:
  - On `main`/`om`, `segment_lesions` is stubbed.
  - Member 2's branch (`origin/Sanmit-Patil`) contains U-Net lesion segmentation in `src/vision/segmentation/` and `ai_models/segmentation/dataset.py`.
- **Explainability (`ai_models/explainability/`)**:
  - Member 3's branch (`origin/Siddhi-Garg`) contains full implementations of `GradCAM` in `gradcam.py` and temperature scaling in `calibration.py`.
- **Image Quality (`computer_vision/image_quality/`)**:
  - Member 2's branch contains quality assessment in `src/vision/quality.py` checking sharpness, illumination, contrast, and field definition.

### 3.4 MATLAB & Simulink
- **MATLAB Integration**:
  - `api_connector.m`: Stubs REST call to backend.
  - `python_bridge.m`: Stubs direct Python in-process call.
  - `data_exchange.m`: Stubs JSON/struct data normalization.
- **Simulink Simulation**:
  - `simulink/README.md` documents that binary `.slx` models are not fabricated in the scaffold.
  - Scenario scripts define placeholders for normal workflow, high volume, and poor-quality recapture.
- **Toolbox & Environment Verification**:
  - Neither `matlab` nor `simulink` are installed on the execution host.
  - SimEvents toolbox availability cannot be confirmed locally. All MATLAB/Simulink files must remain cleanly decoupled from core web/API execution so that missing MATLAB licenses do not break Python/React pipelines.

### 3.5 Docker & Environment
- **`Dockerfile`**:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements-backend.txt .
  RUN pip install --no-cache-dir -r requirements-backend.txt
  COPY backend backend
  COPY integration integration
  COPY ai_models ai_models
  COPY computer_vision computer_vision
  COPY config config
  EXPOSE 8000
  CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
  *Defect*: Copies `ai_models` and `integration` but only installs `requirements-backend.txt`. Python packages `torch`, `torchvision`, `opencv-python-headless`, `numpy`, `pandas`, `scikit-learn` are omitted, making in-container ML execution impossible.
- **`docker-compose.yml`**:
  - Service `db` (PostgreSQL 16) with health check `pg_isready`.
  - Exposes port 5432.
  - No backend web service is defined in `docker-compose.yml` (only the database is orchestrated).

---

## 4. Git Safety & Branch Audit

### 4.1 Branch Inventory
| Branch Name | Location | Commit Hash | Subject / Purpose |
| :--- | :--- | :--- | :--- |
| `main` | Local / Remote | `05f62f6` | Upstream production/stable trunk |
| `om` | Local / Remote | `05f62f6` | Current active working branch (tracking `origin/om`) |
| `origin/Shourya-Thorat` | Remote only | `968ffcd` | Member 1: DR Classifier (EfficientNet-B0) |
| `origin/Sanmit-Patil` | Remote only | `d9cc508` | Member 2: Image Quality & U-Net Lesion Segmentation |
| `origin/Siddhi-Garg` | Remote only | `6672e67` | Member 3: Grad-CAM & Confidence Calibration |

### 4.2 Branch Discrepancy Note
The prompt defines Member 4's working branch as `integration/member-4`. The repository was previously cloned and explicitly switched to `om` per user command. In accordance with strict Git Safety rules, **no silent branch switching or renaming was performed**. A recommendation is submitted in Section 8 to formalize `om` as Member 4's branch or create `integration/member-4` with user approval.

### 4.3 Divergence Analysis (Crucial Finding)
Commit `dea8a27` introduced the modular monolith directory structure on `main`.
- **Member 1 (`origin/Shourya-Thorat`)** branched from `cf024bc` (the initial repository commit), omitting the scaffold. When adding `src/`, Member 1's commit deleted all scaffold directories. **Under no circumstances should `origin/Shourya-Thorat` be merged directly into `main` or `om` without cherry-picking and refactoring into `ai_models/classification/`.**
- **Member 2 (`origin/Sanmit-Patil`)** preserved the scaffold but also introduced `src/vision/`.
- **Member 3 (`origin/Siddhi-Garg`)** correctly utilized `ai_models/explainability/`.

---

## 5. Test Suite Execution & Verification Results

All tests were executed using standard Python and Pytest tooling:

1. **Scaffold Directory Validation**:
   - Command: `python scripts/validate_project.py`
   - Result: `Scaffold validation passed.` (Exit code: 0)
2. **Environment Directory Verification**:
   - Command: `python scripts/setup_environment.py`
   - Result: `Project directories checked.` (Exit code: 0)
3. **Unit Smoke Test**:
   - Command: `python -m pytest tests/unit/test_project_smoke.py`
   - Result: `1 passed in 0.45s` (Exit code: 0)
4. **Backend Health Endpoint Test**:
   - Command: `python -m pytest backend/tests/test_health.py`
   - Result: `1 passed in 1.05s` (Exit code: 0)
5. **End-to-End Pipeline Test**:
   - Command: `python -m pytest tests/end_to_end/test_complete_screening.py`
   - Result: `1 skipped in 0.06s` (Reason: *Enable after the integrated screening pipeline is implemented.*)

**Summary**: 2 passed, 1 skipped, 0 failed.

---

## 6. Audit Conclusion & Phase 0 Recommendation

The EYERIS repository is structurally sound as a modular scaffold. The primary risks are branch structural divergence from Member 1 and missing dependency configurations in Docker. Phase 0 audit is complete and validated. Phase 1 may proceed once the branch confirmation and interface contracts are formally ratified.

