# EYERIS — Phase Plan & Integration Roadmap
**Role**: Senior Software Architect, Technical Lead & Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System  
**Problem Statement**: SIH PS26038  
**Date**: November 2026  
**Status**: Proposal for Team Review  

---

## 1. Executive Summary & Context

As Technical Lead and Integration Engineer (Member 4), this Phase Plan outlines the complete development, integration, verification, and deployment lifecycle for **EYERIS**. The plan bridges the specialized contributions of Member 1 (Classification), Member 2 (Quality & Segmentation), and Member 3 (Explainability & Calibration) into a unified, reliable, clinical-screening-support platform.

Detailed findings from Phase 0 are documented in:
- [Repository Audit Report](file:///c:/Users/ASUS/Desktop/Eyeris/docs/member4_phase0_audit.md)
- [Architecture Validation & Interface Contract](file:///c:/Users/ASUS/Desktop/Eyeris/docs/member4_architecture_validation.md)
- [Integration Risk Register](file:///c:/Users/ASUS/Desktop/Eyeris/docs/member4_integration_risk_register.md)

---

## 2. Phase-by-Phase Implementation Roadmap

```
+---------------------------------------------------------------------------------+
| PHASE 0: Audit, Architecture Validation & Integration Foundation (CURRENT)      |
| Deliverables: Audit Report, Contract Amendment, Risk Register, Phase Plan       |
+----------------------------------------+----------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
| PHASE 1: Core Integration Infrastructure & Backend Foundation                   |
| - Finalize branch naming and Git tracking strategy                              |
| - Implement Pydantic V2 schemas for all screening stages                       |
| - Implement database models, Alembic migrations, and repository layer           |
| - Build mock pipeline orchestrator enabling frontend/API testing without weights|
| - Update Dockerfile and Docker Compose to support both API and ML workloads    |
+----------------------------------------+----------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
| PHASE 2: Pipeline Orchestration & Defensive Error Handling                     |
| - Implement `integration/pipeline.py` and `integration/model_orchestrator.py`  |
| - Implement `integration/decision_engine.py` with referral/recapture policy     |
| - Implement `integration/report_generator.py` (JSON summary + exportable view) |
| - Implement central error codes and fallback degradations in `error_handler.py`|
+----------------------------------------+----------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
| PHASE 3: Subsystem Harvesting & Model Adapter Integration                       |
| - Harvest Member 1's EfficientNet-B0 into `ai_models/classification/`          |
| - Harvest Member 2's Quality & U-Net into `computer_vision/` & `segmentation/`  |
| - Integrate Member 3's Grad-CAM & Calibration into `ai_models/explainability/` |
| - Verify end-to-end tensor transformations on CPU and CUDA                      |
+----------------------------------------+----------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
| PHASE 4: Frontend Development & Clinical UI Integration                        |
| - Build Retinal Image Upload Dropzone with client-side validation              |
| - Implement Results Dashboard with DR Grade Card (0–4) & Confidence Gauge      |
| - Implement Interactive Grad-CAM Overlay with opacity control slider           |
| - Implement Lesion Segmentation toggle layers and Clinical Referral Banner     |
| - Connect frontend services to `/api/v1/screenings` REST endpoints            |
+----------------------------------------+----------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
| PHASE 5: MATLAB Application & Simulink Workflow Simulation                     |
| - Implement `matlab/integration/api_connector.m` connecting to FastAPI backend |
| - Build MATLAB App Designer interface for research image inspection            |
| - Implement SimEvents clinic queuing model (`screening_workflow.slx`)          |
| - Execute simulation scenarios (normal, high volume, poor quality recapture)   |
+----------------------------------------+----------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
| PHASE 6: End-to-End Verification, Performance Optimization & Final Release      |
| - Un-skip and pass `tests/end_to_end/test_complete_screening.py`               |
| - Conduct load and latency profiling on end-to-end inference                   |
| - Finalize comprehensive project documentation and deployment guide            |
| - Create final release tag and demonstration materials                         |
+---------------------------------------------------------------------------------+
```

---

## 3. Phase 1 Prerequisites & Readiness Gate

Before initiating Phase 1 development, the following prerequisites must be fulfilled:

### 3.1 Git & Branch Decision
1. **Branch Confirmation**: Confirm whether Member 4 continues on branch **`om`** (active and tracking `origin/om`) or creates/switches to **`integration/member-4`**.
2. **Feature Branch Isolation**: Confirm that all team members push exclusively to their designated feature branches:
   - Member 1: `feature/classifier` or `Shourya-Thorat`
   - Member 2: `feature/quality-segmentation` or `Sanmit-Patil`
   - Member 3: `feature/explainability` or `Siddhi-Garg`
   - Member 4: `om` or `integration/member-4`

### 3.2 Interface Contract Ratification
The team must formally ratify the amended interface contract in [docs/member4_architecture_validation.md](file:///c:/Users/ASUS/Desktop/Eyeris/docs/member4_architecture_validation.md#22-proposed-interface-contract-amendment-v10-formal), specifically agreeing to:
- 5-class integer grade mapping (`0` to `4`).
- Separation of `raw_probabilities` from `calibrated_confidence`.
- Explicit uncertainty score definition.
- Quality assessment response format and rejection reasons.

### 3.3 Dependencies & Environment Approval
- Approve updating `Dockerfile` to include ML dependencies from `requirements-ml.txt`.
- Approve local development environment installation of `requirements-dev.txt` and `requirements.txt`.

---

## 4. Phase 1 Acceptance Criteria

Phase 1 will be considered complete when:
1. [ ] **Backend Health Endpoint**: `/api/v1/health` verifies application status and reports database readiness without unhandled exceptions.
2. [ ] **Screening Submission Endpoint**: `POST /api/v1/screenings` accepts a fundus image (JPEG/PNG), stores the file securely in `./storage/`, creates a database record, and returns a tracking `case_id`.
3. [ ] **Mock Pipeline Orchestrator**: An in-memory mock pipeline executes successfully end-to-end, returning synthetic valid screening payloads conforming strictly to the Interface Contract.
4. [ ] **Screening Retrieval Endpoint**: `GET /api/v1/screenings/{case_id}` returns the complete screening state and mock result payload.
5. [ ] **Database Persistence**: Alembic baseline migration generates the `screening_records` table, verified against PostgreSQL.
6. [ ] **Automated Test Suite**: Unit tests covering Pydantic schemas, API endpoints, and storage management pass with 100% success rate.

