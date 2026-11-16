# EYERIS — Phase 1.1 Remaining Blockers & Technical Debt Register
**Subsystem**: Integration Governance & Risk Tracking  
**Role**: Senior Software Architect & Integration Lead (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Living Register for Phase 2  

---

## 1. Remaining Technical & Integration Blockers

| Issue ID | Subsystem | Description & Impact | Current Status | Resolution Strategy for Phase 2 |
| :--- | :--- | :--- | :--- | :--- |
| **ISS-01** | **Member 1 Model Harvesting** | Member 1 (`origin/Shourya-Thorat`) developed classification in `src/model.py` and `src/predict.py`. Model weights (`checkpoints/best_model.pth` or `.pt`) need to be formalized and loaded via `ai_models/classification/model.py`. | Documented | In Phase 2, harvest `build_efficientnet_b0` and `predict_retinopathy` into `ai_models/classification/predict.py` with automatic CPU/CUDA detection and weight checkpoint loading. |
| **ISS-02** | **Member 2 Quality & U-Net Adapter** | Member 2 (`origin/Sanmit-Patil`) implemented quality in `src/vision/quality.py` and segmentation in `src/vision/segmentation/`. | Documented | Consolidate `RetinalQualityAssessor` into `computer_vision/image_quality/` and U-Net weights loader into `ai_models/segmentation/predict.py`. |
| **ISS-03** | **Member 3 Grad-CAM & Calibration Adapter** | Member 3 (`origin/Siddhi-Garg`) implemented Grad-CAM and temperature scaling in `ai_models/explainability/`. | Documented | Connect `compute_gradcam` to the harvested Member 1 classification model instance in `ai_models/explainability/gradcam.py`. |
| **ISS-04** | **Local PostgreSQL Service Inactive** | PostgreSQL is not currently running on `localhost:5432`. Health check correctly reports `database_connected: false` and degraded status when accessed outside test fixtures. | Controlled | Spin up PostgreSQL container via `docker compose up -d db` and run initial Alembic migrations. |
| **ISS-05** | **MATLAB & SimEvents Absence on Host** | MATLAB executable is not present on the host PATH. SimEvents license cannot be verified locally. | Decoupled | Retain MATLAB integration as strictly complementary via `/api/v1` REST endpoints (`api_connector.m`). Mock simulation outputs for CI/CD environments. |
| **ISS-06** | **Final Visual Design & UI Polish Gate** | Frontend foundation is functional and responsive, but visual design is deliberately unbranded pending user review of the UI/UX Research Gate deliverables. | Gated | Implement approved color tokens, dual-pane Grad-CAM canvas, and styling polish during Phase 2. |

---

## 2. Phase 2 Readiness Criteria

Phase 2 can begin once:
1. The user reviews and approves this Phase 1.1 verification and remediation report.
2. The user grants explicit approval to commit and push changes to `om`.
3. Model weight artifacts are placed in `artifacts/model_registry/` for deep learning inference.

