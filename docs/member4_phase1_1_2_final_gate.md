# EYERIS — Phase 1.1.2 Final Commit Gate & Evidence Report
**Role**: Independent QA, Release Reviewer & Integration Lead (Member 4)  
**Date**: November 16, 2026  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System (SIH Problem Statement PS26038)  
**Target Branch**: `om`  
**Current HEAD Commit**: `74bf48f` (`feat(member-4): complete Phase 1.1 remediation, frontend foundation, resilient DB handling, and clinical safety validations`)  
**Tracking Status**: Up-to-date with `origin/om`  
**Gate Verdict**: **READY FOR COMMIT REVIEW** (with documented limitations)

---

## 1. Git Evidence

### 1.1 Command Outputs
- **`git branch --show-current`**:
  ```
  om
  ```
- **`git status --short`**:
  ```
  (No output - working tree clean)
  ```
- **`git diff --stat`**:
  ```
  (No output - zero unstaged changes)
  ```
- **`git diff --cached --stat`**:
  ```
  (No output - zero staged changes)
  ```
- **`git diff --check`**:
  ```
  (No output - zero whitespace/merge artifact errors)
  ```
- **`git ls-files --others --exclude-standard`**:
  ```
  (No output - zero untracked files)
  ```

### 1.2 Working Tree Status
- **Staged Files**: None.
- **Unstaged Modifications**: None.
- **Untracked Files**: None.
- **Working Tree**: Completely clean and synchronized with remote `origin/om` at commit `74bf48f`.

---

## 2. Test Evidence

### 2.1 Pytest Suite Execution
Command:
```powershell
python -m pytest tests/unit backend/tests -v
```
Output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0 -- C:\Program Files\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ASUS\Desktop\Eyeris
configfile: pytest.ini
plugins: anyio-4.12.1, Faker-40.37.0, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 17 items

tests/unit/test_decision_engine.py::test_decision_engine_quality_rejection PASSED [  5%]
tests/unit/test_decision_engine.py::test_decision_engine_uncertainty_escalation PASSED [ 11%]
tests/unit/test_decision_engine.py::test_decision_engine_proliferative_dr PASSED [ 17%]
tests/unit/test_decision_engine.py::test_decision_engine_no_dr PASSED    [ 23%]
tests/unit/test_orchestrator.py::test_pipeline_analyse_case_with_mock PASSED [ 29%]
tests/unit/test_orchestrator.py::test_pipeline_analyse_case_safe_default PASSED [ 35%]
tests/unit/test_orchestrator.py::test_pipeline_quality_rejection PASSED  [ 41%]
tests/unit/test_project_smoke.py::test_project_smoke PASSED              [ 47%]
tests/unit/test_schemas.py::test_quality_metrics_validation PASSED       [ 52%]
tests/unit/test_schemas.py::test_screening_response_schema PASSED        [ 58%]
backend/tests/test_health.py::test_health PASSED                         [ 64%]
backend/tests/test_screenings_api.py::test_api_v1_health PASSED          [ 70%]
backend/tests/test_screenings_api.py::test_cors_preflight PASSED         [ 76%]
backend/tests/test_screenings_api.py::test_post_screening_valid_and_retrieval PASSED [ 82%]
backend/tests/test_screenings_api.py::test_post_screening_invalid_file_type PASSED [ 88%]
backend/tests/test_screenings_api.py::test_post_screening_oversized_file PASSED [ 94%]
backend/tests/test_screenings_api.py::test_get_nonexistent_screening PASSED [100%]

============================== warnings summary ===============================
backend/tests/test_screenings_api.py::test_post_screening_oversized_file
  C:\Users\ASUS\AppData\Roaming\Python\Python314\site-packages\fastapi\routing.py:352: DeprecationWarning: 'HTTP_413_REQUEST_ENTITY_TOO_LARGE' is deprecated. Use 'HTTP_413_CONTENT_TOO_LARGE' instead.
    return await dependant.call(**values)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 17 passed, 1 warning in 1.98s ========================
```
- **Exit Code**: `0`
- **Result Summary**: 17 passed, 0 failures, 1 deprecation warning.

### 2.2 Project Scaffold Validation
Command:
```powershell
python scripts/validate_project.py
```
Output:
```
Scaffold validation passed.
```
- **Exit Code**: `0`

### 2.3 Frontend Production Build
Command:
```powershell
npm run build --prefix frontend
```
Output:
```
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
✓ built in 1.13s
```
- **Exit Code**: `0`

---

## 3. Clinical Policy Evidence & Threshold Status

### 3.1 Policy Rule Base and Code References

| Policy Parameter | Code Reference | Implementation in Code | Validation Status |
| :--- | :--- | :--- | :--- |
| **Quality Threshold (0.60)** | `integration/decision_engine.py:17` | `if not quality.get("is_gradable", True) or quality.get("overall_quality_score", 1.0) < 0.6:` | **Provisional Engineering Default** — Not clinically validated. `docs/decision_policy.md` explicitly records: *"Thresholds remain unset until justified and validated."* Requires clinical dataset calibration. |
| **Uncertainty Threshold (0.35)** | `integration/decision_engine.py:43` | `if is_uncertain or uncertainty > 0.35:` | **Provisional Engineering Default** — Not clinically validated. Requires Monte Carlo dropout entropy tuning against expert arbitration labels. |
| **Manual Review Behavior** | `integration/decision_engine.py:27-34` | `if not classification: return {"referral_recommended": False, "review_required": True, "urgency": "manual_review"}` | **Approved Safety Rule** — Decoupled from hospital referral queue to prevent false referable DR positives. |
| **Referral Behavior** | `integration/decision_engine.py:51-72` | Grades 2, 3, 4 recommend referral (`routine_referral`, `prompt_referral`, `urgent_referral`). | **Provisional Clinical Guideline** — Follows ICDR staging recommendations. |
| **Ungradable Image Behavior** | `integration/decision_engine.py:17-25` | Halts grading; returns `referral_recommended: False`, `urgency: "recapture_required"`. | **Approved Safety Rule** — Reassuring grade is never assigned to poor-quality images. |
| **Missing-Model Behavior** | `integration/model_orchestrator.py:60-63` | `if not allow_mock: return None` | **Approved Safety Rule** — Strict absence of prediction fabrication when real model weights are not loaded. |
| **Mock Output Behavior** | `integration/model_orchestrator.py:65-78` | Returns `is_mock: True` and version `"mock-synthetic-v0"` only if `allow_mock=True` is explicitly passed in config. | **Approved Safety Rule** — Synthetic data disabled by default in production. |

---

## 4. API Test Coverage Matrix

| Endpoint / Behavior | Test Name / Location | Result |
| :--- | :--- | :--- |
| **Health Check** | `backend/tests/test_health.py::test_health` and `backend/tests/test_screenings_api.py::test_api_v1_health` | **PASSED** |
| **Readiness Check** | *None* (No dedicated `/ready` or `/api/v1/ready` endpoint implemented) | **NOT TESTED** |
| **Fundus Image Upload** | `backend/tests/test_screenings_api.py::test_post_screening_valid_and_retrieval` | **PASSED** |
| **Invalid File Type Rejection** | `backend/tests/test_screenings_api.py::test_post_screening_invalid_file_type` (text/plain yields HTTP 400) | **PASSED** |
| **Oversized Upload Rejection** | `backend/tests/test_screenings_api.py::test_post_screening_oversized_file` (16MB yields HTTP 413) | **PASSED** |
| **Screening History List** | `backend/tests/test_screenings_api.py::test_post_screening_valid_and_retrieval` (calls `GET /api/v1/screenings`) | **PASSED** |
| **Screening Details** | `backend/tests/test_screenings_api.py::test_post_screening_valid_and_retrieval` (calls `GET /api/v1/screenings/{case_id}`) | **PASSED** |
| **Report Retrieval** | `backend/tests/test_screenings_api.py::test_post_screening_valid_and_retrieval` (calls `GET /api/v1/screenings/{case_id}/report`) | **PASSED** |
| **Explanation Retrieval** | `backend/tests/test_screenings_api.py::test_post_screening_valid_and_retrieval` (calls `GET /api/v1/screenings/{case_id}/explanation`) | **PASSED** |
| **Database Unavailable (503)** | *None* (No test fixture specifically injects connection failure into `get_db`) | **NOT TESTED** |
| **CORS Preflight** | `backend/tests/test_screenings_api.py::test_cors_preflight` (OPTIONS request with Access-Control headers) | **PASSED** |

---

## 5. Dependency and Database Evidence

### 5.1 Psycopg Requirement
- **File**: `requirements-backend.txt` (referenced via `-r requirements-backend.txt` in `requirements.txt`)
- **Exact Line**:
  ```text
  psycopg[binary]>=3.1
  ```

### 5.2 Database Configuration & Fallback Elimination
- **File**: `backend/app/db/session.py`
- **Lines 18-28**:
  ```python
  db_url = os.environ.get("DATABASE_URL", settings.database_url)
  if _engine is None or str(_engine.url) != db_url:
      connect_args = {}
      if db_url.startswith("sqlite"):
          connect_args["check_same_thread"] = False
          _engine = create_engine(db_url, connect_args=connect_args)
      else:
          # PostgreSQL / External DB: Never silently fallback to SQLite!
          _engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
      _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
  ```
- **Confirmation**: SQLite is used **only** when `DATABASE_URL` explicitly begins with `sqlite:`. Non-SQLite URLs instantiate standard pooled PostgreSQL engines with zero silent fallback to local SQLite.

### 5.3 Test Database Isolation
- **File**: `tests/conftest.py`
- **Lines 5-7**:
  ```python
  # Explicitly configure test database for test suite isolation
  TEST_DB_PATH = Path("./storage/test_screening.db").resolve()
  os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
  ```
- **Confirmation**: `tests/conftest.py` executes before any test module is imported, overriding `DATABASE_URL` in the environment to a dedicated local SQLite path (`./storage/test_screening.db`). The test suite cannot inadvertently connect to or mutate a production PostgreSQL database.

---

## 6. Docker Validation Status

- **Docker Version Output**:
  ```
  Docker version 29.7.2, build a7dcaa6
  ```
- **Docker Daemon Probe Output**:
  ```
  failed to connect to the docker API at npipe:////./pipe/docker_engine; check if the path is correct and if the daemon is running: open //./pipe/docker_engine: The system cannot find the file specified.
  ```
- **Status**: **NOT TESTED**
- **Note**: The Docker CLI is installed, but the Docker Desktop engine is not running on the local Windows host. Therefore, live container image building has not been executed and no false claims of container validation are made.

---

## 7. Limitations & Downstream Dependencies

1. **Downstream Subsystems**:
   - Member 1 Classifier weights (`best_model.pth`) are not present. The system safely returns `classification=None` and status `"pending_review"`.
   - Member 2 Segmentation weights (`unet_dr.pth`) are not present. Lesion segmentation returns `None`.
   - Member 3 Explainability & Calibration matrices are not present. Grad-CAM and uncertainty scores return safe fallbacks.
2. **Provisional Heuristics**:
   - Quality threshold (0.60) and uncertainty threshold (0.35) are engineering heuristics and must not be presented as clinically validated diagnostic criteria.
3. **Untested Integration Edge Cases**:
   - Readiness endpoint (`/ready`) is not implemented.
   - Live HTTP 503 database unavailability simulation is not part of the automated test suite.
   - Containerized runtime build is untested due to host daemon being offline.

---

## 8. Final Verdict

```
================================================================================
FINAL VERDICT: READY FOR COMMIT REVIEW
================================================================================
The Phase 1.1 implementation and Git state have been rigorously verified.
Working tree is clean, test suites pass (17/17), frontend build succeeds,
and clinical policies, provisional thresholds, and limitations are fully
documented and transparently reported.
================================================================================
```

