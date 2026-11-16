# EYERIS — Phase 1.1 Architecture & Safety Review
**Subsystem**: Technical Architecture, AI Safety & Data Governance  
**Role**: Senior Software Architect & Integration Lead (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Formal Review Deliverable  

---

## 1. AI Orchestration Safety Review

### 1.1 The Mock Masquerading Hazard
In complex multi-agent and multi-engineer healthcare software development, a dangerous anti-pattern occurs when fallback mock stubs return plausible synthetic diagnostic data (e.g. `predicted_grade: 2`, `confidence: 0.824`) during normal runtime. If model weights are missing or uninitialized, operators and testers can mistake fabricated synthetic numbers for genuine deep learning inference.

### 1.2 Remediated Orchestrator Architecture
In `integration/model_orchestrator.py`:
1. **Strict Default Isolation**: All stages (`_run_classification_stage`, `_run_segmentation_stage`, `_run_explainability_stage`) accept an explicit `config` dictionary. The parameter `allow_mock` defaults strictly to `False`.
2. **Explicit Unavailable State**: When `predict_grade` is absent, unweighted, or raises `NotImplementedError`, the orchestrator returns `None` for the classification stage. It does **not** invent a grade or confidence score.
3. **Status Decoupling**:
   - If real classification inference completes: `status = "completed"`.
   - If image is technically ungradable: `status = "rejected_quality"`.
   - If image is gradable but model inference is unavailable: `status = "pending_review"` with `classification: null`.
4. **Mock Isolation for Controlled Tests**: Synthetic mock results are only returned when an automated test explicitly passes `config={"allow_mock": True}`. In that scenario, the payload includes an unambiguous flag: `"is_mock": True` and `"model_version": "mock-synthetic-v0"`.

---

## 2. Clinical Decision Policy Review

### 2.1 Alignment with `docs/decision_policy.md`
The clinical decision engine (`integration/decision_engine.py`) enforces strict safety invariants:

| Condition | Automated Action | Urgency Tier | Clinical Output |
| :--- | :--- | :--- | :--- |
| **Ungradable Image** ($<0.60$ quality score or severe blur/glare) | Halts deep inference immediately. | `recapture_required` | `referral_recommended = False`. Mandates immediate camera repositioning/recapture. Never gives a reassuring "No DR" conclusion. |
| **Missing / Unimplemented Model** | Bypasses automated grading. | `manual_review` | `referral_recommended = True`. Conservative default routing patient to clinician for comprehensive examination. |
| **High Model Uncertainty** ($>0.35$ uncertainty score or `is_uncertain = True`) | Overrides normal thresholding. | `urgent_review` | `referral_recommended = True`. Flags high epistemic ambiguity requiring human specialist confirmation. |
| **Grade 4 (Proliferative DR)** | High vision-loss risk triage. | `urgent_referral` | Urgent referral within 1–2 weeks to retina specialist. |
| **Grade 3 (Severe NPDR)** | High referral priority. | `prompt_referral` | Prompt referral within 2–4 weeks to ophthalmologist. |
| **Grade 2 (Moderate NPDR)** | Standard referable DR threshold. | `routine_referral` | Routine referral within 4–8 weeks for dilated examination. |
| **Grade 1 (Mild NPDR)** | Non-referable microaneurysms. | `routine_monitoring` | Rescreen in 6–12 months. Reinforce glycemic control. |
| **Grade 0 (No DR)** | Clear retina. | `annual_screening` | Rescreen in 12–24 months per national diabetes guidelines. |

### 2.2 Unresolved Clinical Policy Questions
1. **Bilateral Contradiction Policy**: If one eye is Grade 0 and the fellow eye is Grade 3, the overall patient-level referral must escalate to the worst-eye grade (Grade 3). The single-image pipeline must be extended in Phase 2 to support bilateral Left/Right eye aggregation.
2. **Macular Edema Co-existence**: The current ICDR scale evaluates retinopathy severity, but Diabetic Macular Edema (DME) can cause severe visual impairment even in mild DR. Future phases should incorporate a dedicated DME risk flag.

---

## 3. Database Safety & Connection Governance

### 3.1 Remediated Session Architecture (`backend/app/db/session.py`)
1. **Lazy Engine Instantiation**: `_engine = None` at module load time. No TCP connections or database driver handshakes occur simply by importing `session.py` or `main.py`.
2. **No Silent Fallback**: If `settings.database_url` points to PostgreSQL and the server is offline or credentials fail, the application:
   - Sets health status to `"degraded"` with `"database_connected": false`.
   - On write operations, catches `OperationalError` and raises `HTTP 503 Service Unavailable`.
   - **Never** silently creates a local SQLite file in production.
3. **Explicit Test Environment Isolation**: In `tests/conftest.py`, automated tests explicitly configure `os.environ["DATABASE_URL"] = "sqlite:///./storage/test_screening.db"`, ensuring safe and isolated test runs.

---

## 4. Docker & Multi-Stage Dependency Strategy

### 4.1 Dependency Separation Architecture
To avoid shipping heavy PyTorch CUDA binaries ($>2$ GB) in lightweight web containers, three distinct dependency profiles are established:
1. `requirements-backend.txt`: FastAPI, Uvicorn, SQLAlchemy, Psycopg, Pydantic, Pillow. (Lightweight, fast cold-starts).
2. `requirements-ml.txt`: NumPy, Pandas, Scikit-learn, OpenCV-headless, PyTorch, Torchvision. (Inference workers).
3. `requirements-dev.txt`: Pytest, Flake8, Black, HTTPX. (CI/CD only).

The application starts and passes health probes cleanly without model weights or GPU drivers present.

