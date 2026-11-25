# EYERIS — Phase 0 Integration Risk Register
**Role**: Senior Software Architect, Technical Lead & Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System  
**Problem Statement**: SIH PS26038  
**Date**: November 2026  
**Status**: Active Living Document  

---

## 1. Overview

This Risk Register tracks technical, architectural, algorithmic, and operational risks across all four sub-teams of the EYERIS project. Each identified risk is evaluated with respect to **Impact**, **Likelihood**, and actionable **Mitigation/Prevention**, assigning clear ownership to ensure seamless final integration.

---

## 2. Risk Matrix

| Risk ID | Risk Description | Category | Impact | Likelihood | Mitigation / Prevention Strategy | Responsible |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | **Member 1 Branch Structural Divergence**: `origin/Shourya-Thorat` branched from initial commit `cf024bc` without the scaffold, deleting all backend/frontend/integration directories and creating a flat `src/`. | Git / Architecture | **CRITICAL** | **HIGH** | **Never merge `origin/Shourya-Thorat` directly.** Member 4 will isolate the classification model and weights, encapsulate them into `ai_models/classification/model.py` and `predict.py`, and preserve the modular scaffold. | Member 4 & Member 1 |
| **RSK-02** | **Image Preprocessing Mismatch**: Member 1 (Classifier), Member 2 (Segmentation), and Member 3 (Grad-CAM) use differing resizing interpolation, color spaces (RGB vs BGR), or normalization statistics (ImageNet vs raw $[0, 1]$). | ML / Computer Vision | **HIGH** | **HIGH** | Centralize image preprocessing in `computer_vision/preprocessing/` and `ai_models/common/transforms.py`. Mandate that all model adapters consume standard RGB uint8 arrays or standard normalized tensors defined in `docs/member4_architecture_validation.md`. | Member 4 & Member 2 |
| **RSK-03** | **Class Label & Indexing Discrepancy**: Risk of 1-based indexing ($1\dots5$) vs 0-based indexing ($0\dots4$) or differing grade nomenclature ("No DR" vs "Normal", "Proliferative" vs "PDR"). | ML / Integration | **HIGH** | **MEDIUM** | Enforce single source of truth in `ai_models/common/labels.py` (`DR_GRADE_LABELS = {0: "No DR", 1: "Mild", 2: "Moderate", 3: "Severe", 4: "Proliferative DR"}`). Validate output types in `integration/result_formatter.py`. | Member 4 & Member 1 |
| **RSK-04** | **Conflation of Raw Logits, Probabilities & Clinical Decisions**: Risk of treating raw uncalibrated Softmax probabilities as diagnostic certainties or conflating model probability with referral threshold. | Clinical / Safety | **HIGH** | **HIGH** | Separate fields in schema: `raw_probabilities`, `calibrated_confidence`, `uncertainty_score`, and `referral_recommended`. Document that classification output $\neq$ diagnosis. Enforce decision policy thresholds in `integration/decision_engine.py`. | Member 4 & Member 3 |
| **RSK-05** | **Dockerfile Dependency Omission**: Existing `Dockerfile` installs `requirements-backend.txt` but omits `requirements-ml.txt`, causing container crash upon pipeline execution. | DevOps / Deployment | **HIGH** | **HIGH** | Update `Dockerfile` to install unified dependencies (`requirements.txt`) or configure multi-stage builds separating API gateway from heavy ML inference workers. | Member 4 |
| **RSK-06** | **CPU / GPU Device Incompatibility**: Trained models attempting `.cuda()` execution on host machines or cloud containers without dedicated NVIDIA GPUs, throwing runtime exceptions. | System / Runtime | **HIGH** | **MEDIUM** | In all model loaders (`model_loader.py`, `predict.py`), enforce explicit device detection: `device = torch.device("cuda" if torch.cuda.is_available() else "cpu")` and map weights with `torch.load(..., map_location=device)`. | Member 1, 2, 3, 4 |
| **RSK-07** | **Large Fundus Image Memory Exhaustion**: High-resolution retinal fundus images ($3000 \times 3000+$) causing Out-Of-Memory (OOM) errors during simultaneous U-Net segmentation and Grad-CAM backprop. | Performance | **HIGH** | **MEDIUM** | Enforce client-side/gateway resizing to maximum $1024 \times 1024$ before deep inference; implement memory-efficient inference using `torch.no_grad()` where backprop is not needed; run garbage collection after Grad-CAM generation. | Member 4 & Member 2 |
| **RSK-08** | **Synchronous Database Failure at Startup**: `backend/app/db/session.py` instantiates `create_engine` at module level; if PostgreSQL is down, API container/process fails immediately on boot. | Backend / Resilience | **MEDIUM** | **HIGH** | Implement graceful database error handling and health check readiness probes. Ensure `/api/v1/health` checks DB connectivity without crashing the web process. | Member 4 |
| **RSK-09** | **MATLAB & Simulink License / Dependency Failure**: Host systems running without MATLAB or without SimEvents toolbox throwing missing license / runtime errors. | External Tooling | **MEDIUM** | **HIGH** | Maintain MATLAB and Simulink files as strictly complementary components. Never import MATLAB libraries into the core Python/FastAPI runtime. Mock simulation data if SimEvents license is absent during CI. | Member 4 |
| **RSK-10** | **Uncertainty & Abstention Threshold Ambiguity**: Undefined clinical threshold for when high model entropy / epistemic uncertainty should trigger mandatory specialist referral or image recapture. | Clinical / Integration | **MEDIUM** | **MEDIUM** | Codify uncertainty criteria in `config/decision_policy.yaml`: if `uncertainty_score > uncertainty_threshold` OR `overall_quality_score < quality_threshold`, automatically set `status = "escalated_for_human_review"` and flag case for clinician review. | Member 4 & Member 3 |
| **RSK-11** | **Alembic Database Migration Drift**: Database schema modifications made directly to models without generated Alembic migration versions, breaking deployments. | Backend / DB | **MEDIUM** | **LOW** | Create initial baseline Alembic revision (`alembic revision --autogenerate -m "initial_schema"`) during Phase 1. Forbid manual DDL execution. | Member 4 |
| **RSK-12** | **Frontend/Backend Schema Naming Inconsistencies**: Frontend expecting `camelCase` (e.g. `caseId`, `drGrade`) while FastAPI returns `snake_case` (e.g. `case_id`, `dr_grade`), resulting in `undefined` UI displays. | Frontend / API | **MEDIUM** | **HIGH** | Formalize Pydantic V2 schemas with camelCase aliases (`model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)`) or standardize frontend consumption via TypeScript/JSDoc types matching snake_case. | Member 4 |

---

## 3. Risk Monitoring & Action Protocol

1. **Daily Standup Review**: Check active feature branches against the Interface Contract.
2. **Pre-Merge Review**: Member 4 must verify that no PR introduces breaking changes to `integration_contract.md`.
3. **Automated CI Check**: Smoke tests and integration tests must run against mock tensors to guarantee zero dependency breakage.

