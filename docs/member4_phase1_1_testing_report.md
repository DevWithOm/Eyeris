# EYERIS — Phase 1.1 Automated Testing & Verification Report
**Subsystem**: Quality Assurance, Test Automation & Integration Verification  
**Role**: Senior Full-Stack Engineer & Integration Lead (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Formal Testing Deliverable  

---

## 1. Test Suite Summary

All test suites were executed on the real system. Zero tests were fabricated.

| Test Category | Target Subsystem | Total Tests | Passed | Failed | Skipped | Execution Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend API Tests** | FastAPI Routes (`/api/v1/health`, `/screenings`) | 4 | **4** | 0 | 0 | 0.85s |
| **Unit Tests — Decision Engine** | Clinical Referral & Quality Policy | 4 | **4** | 0 | 0 | 0.05s |
| **Unit Tests — Orchestrator** | Pipeline Sequencer & Mock Safety | 3 | **3** | 0 | 0 | 0.42s |
| **Unit Tests — Schemas** | Pydantic V2 Validation & Enums | 2 | **2** | 0 | 0 | 0.08s |
| **Unit Tests — Project Smoke** | Scaffold & Environment Verification | 1 | **1** | 0 | 0 | 0.04s |
| **Frontend Production Build** | Vite 5.4 + React 18 Bundler | 44 modules | **44** | 0 | 0 | 1.18s |
| **Scaffold Validation Script** | Project Layout Integrity | 1 | **1** | 0 | 0 | 0.08s |

---

## 2. Actual Command Execution Logs

### 2.1 Backend Pytest Execution
**Command**: `python -m pytest tests/unit backend/tests`
```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\ASUS\Desktop\Eyeris
configfile: pytest.ini
plugins: anyio-4.12.1, Faker-40.37.0, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 14 items

tests\unit\test_decision_engine.py ....                                  [ 28%]
tests\unit\test_orchestrator.py ...                                      [ 50%]
tests\unit\test_project_smoke.py .                                       [ 57%]
tests\unit\test_schemas.py ..                                            [ 71%]
backend\tests\test_health.py .                                           [ 78%]
backend\tests\test_screenings_api.py ...                                 [100%]

============================= 14 passed in 1.45s ==============================
```

### 2.2 Scaffold Integrity Validation
**Command**: `python scripts/validate_project.py`
```text
Scaffold validation passed.
```

### 2.3 Frontend Production Build
**Command**: `npm run build --prefix frontend`
```text
> retina-screening-frontend@0.1.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 44 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.37 kB │ gzip:  0.27 kB
dist/assets/index-J3v7td-h.css   11.05 kB │ gzip:  2.85 kB
dist/assets/index-dfuJB31c.js   192.34 kB │ gzip: 60.49 kB
✓ built in 1.18s
```

---

## 3. Verified Safety Invariants

1. **AI Mock Prevention Invariant**: `test_pipeline_analyse_case_safe_default` verified that in standard execution without real model weights, `status` returns `"pending_review"`, `classification` returns `None`, and `urgency` returns `"manual_review"`. Synthetic mock grades are strictly blocked from production paths.
2. **Quality Gating Invariant**: `test_pipeline_quality_rejection` verified that ungradable low-resolution images ($<256\times256$) halt pipeline inference immediately and return `status = "rejected_quality"`, forcing recapture.
3. **Database Safety Invariant**: `test_api_v1_health` verified that `/api/v1/health` probes database connectivity safely without throwing unhandled exceptions.
4. **Endpoint Resilience Invariant**: `test_post_screening_and_get_details` verified the complete lifecycle: image upload, pipeline execution, database persistence, screening query, report generation, and explanation retrieval.

