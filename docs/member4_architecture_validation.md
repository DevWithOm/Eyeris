# EYERIS — Phase 0 Architecture Validation & Interface Contract Report
**Role**: Senior Software Architect, Technical Lead & Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System  
**Problem Statement**: SIH PS26038  
**Date**: November 2026  
**Status**: Completed  

---

## 1. System Architecture Overview & Responsibility Separation

The EYERIS system is designed as a **Modular Monolith** supporting research-oriented diabetic retinopathy screening workflows. The architecture enforces clear boundaries between presentation, application serving, pipeline orchestration, specialized algorithmic inference, operational simulation, and external clients.

### 1.1 Architecture Flow Diagram

```
+-------------------------------------------------------------+
|                     PRESENTATION TIER                       |
|  +---------------------------+  +------------------------+  |
|  | React 18 + Vite Web App   |  | MATLAB App Designer    |  |
|  | (Primary User Interface)  |  | (Complementary Client) |  |
|  +-------------+-------------+  +-----------+------------+  |
+----------------|----------------------------|---------------+
                 | HTTP REST                  | HTTP REST (api_connector.m)
                 v                            v
+-------------------------------------------------------------+
|                      BACKEND API TIER                       |
|                     FastAPI (v1 Routes)                     |
|  - Auth & Security Headers                                  |
|  - Request Validation (Pydantic V2)                         |
|  - Multipart File Upload & Storage Management               |
|  - Screening Lifecycle State Machine                        |
|  - PostgreSQL Metadata Persistence                          |
+------------------------------+------------------------------+
                               | In-Process Call
                               v
+-------------------------------------------------------------+
|                 INTEGRATION ORCHESTRATOR                    |
|             (integration.model_orchestrator)                |
|                                                             |
|  Step 1: Quality Assessment (computer_vision.image_quality) |
|          +--> If Quality Reject: Escalate to Recapture     |
|                                                             |
|  Step 2: Preprocessing (computer_vision.preprocessing)      |
|          +--> CLAHE, Green Channel, Aspect Ratio Crop       |
|                                                             |
|  Step 3: DR Classification (ai_models.classification)       |
|          +--> EfficientNet-B0 Grade (0–4) + Probabilities   |
|                                                             |
|  Step 4: Lesion Segmentation (ai_models.segmentation)       |
|          +--> U-Net Exudates, Hemorrhages, MAs Masks        |
|                                                             |
|  Step 5: Explainability (ai_models.explainability)          |
|          +--> Grad-CAM Heatmap + Temperature Calibration   |
+------------------------------+------------------------------+
                               | Normalized Output Struct
                               v
+-------------------------------------------------------------+
|                      DECISION ENGINE                        |
|              (integration.decision_engine)                  |
|  - Referable DR Determination (Grade >= 2 OR High Risk)     |
|  - Uncertainty & Calibrated Confidence Thresholding         |
|  - Actionable Referral / Recapture Recommendation           |
+------------------------------+------------------------------+
                               | Clinical Screening State
                               v
+-------------------------------------------------------------+
|                      REPORT GENERATOR                       |
|              (integration.report_generator)                 |
|  - Formatted Screening Summary (JSON & Exportable PDF/HTML) |
|  - Mandatory Medical Disclaimer & Research Notice           |
+-------------------------------------------------------------+
```

### 1.2 Separation of Concerns Audit

| Layer / Directory | Primary Responsibility | Boundaries & Invariants |
| :--- | :--- | :--- |
| `frontend/` | Web dashboard, image drag-and-drop, interactive inspection, visual report viewing | Must never perform inference or directly touch model weights; communicates exclusively with `/api/v1/` endpoints. |
| `backend/` | REST endpoint routing, request sanitization, storage management, database records | Exposes API contracts, handles HTTP lifecycle, delegates inference tasks to `integration/`. |
| `integration/` | Pipeline orchestration, sequential failure handling, decision logic, report generation | Bridges CV/ML modules with the API; enforces the interface contract; guarantees defensive degradation. |
| `ai_models/` | PyTorch inference engines (Classification, Segmentation, Explainability) | Pure computation functions; expects preprocessed tensors/arrays; stateless. |
| `computer_vision/` | Image QC (blur, illumination, contrast) and preprocessing | Rejects ungradable images early to avoid wasted GPU/CPU inference; returns standardized diagnostic metrics. |
| `matlab/` | Standalone researcher desktop client | Interfaces via `/api/v1/` REST endpoints or in-process Python engine; does not replace the React web app. |
| `simulink/` | Discrete-event screening clinic workflow simulation | Models patient arrival rates, screening queue depth, nurse/specialist throughput, and recapture delays via SimEvents; does **not** train or validate AI models. |

---

## 2. Shared Interface Contract Audit & Proposed Amendment

### 2.1 Audit of Existing `docs/integration_contract.md`
The existing `docs/integration_contract.md` defines four proposed top-level function signatures:
```python
analyse_case(image_path: str, config: dict | None = None) -> dict
assess_quality(image_path: str) -> dict
predict_grade(image_path: str) -> dict
segment_lesions(image_path: str) -> dict
generate_gradcam(image_path: str, model) -> dict
```

#### Deficiencies Identified in Existing Contract:
1. **Ambiguous Types**: Dict return types without explicit schema, field names, or types.
2. **Missing Input Format Specifications**: No formal constraints on color space (RGB vs BGR), resolution limits, bit depth, or aspect ratio.
3. **Conflated Metrics**: Does not clearly distinguish between raw Softmax probability, temperature-calibrated confidence, and referral thresholding.
4. **Uncertainty & Abstention**: Missing explicit schema for uncertainty score and criteria for system abstention.
5. **Quality Assessment Schema**: No numeric sub-scores for sharpness, illumination, or field completeness.
6. **Segmentation Output**: Missing mask dimensions, format (binary mask vs polygon contours), and lesion area quantification.
7. **Model Metadata**: Lacks model identifier, weights version hash, and timestamp tracing.

---

### 2.2 Proposed Interface Contract Amendment (V1.0 Formal)

To ensure Member 1, Member 2, and Member 3 can develop independently without integration breakage, the contract is formalized as follows:

#### A. Standard Input Specifications
- **Accepted Formats**: JPEG, PNG, TIFF.
- **Color Space**: RGB (OpenCV BGR inputs must be converted immediately to RGB).
- **Target Dimensions**: $512 \times 512$ pixels (minimum acceptable: $256 \times 256$, maximum: $4096 \times 4096$).
- **Maximum File Size**: 15 MB.

#### B. Module 1: Image Quality Assessment (`assess_quality`)
```json
{
  "is_gradable": true,
  "overall_quality_score": 0.88,
  "metrics": {
    "sharpness_score": 0.84,
    "illumination_score": 0.92,
    "contrast_score": 0.89,
    "field_definition_score": 0.95
  },
  "rejection_reasons": []
}
```

#### C. Module 2: DR Classification (`predict_grade`)
```json
{
  "predicted_grade": 2,
  "grade_name": "Moderate",
  "raw_probabilities": {
    "0": 0.04,
    "1": 0.12,
    "2": 0.72,
    "3": 0.09,
    "4": 0.03
  },
  "referable_dr": true,
  "model_version": "efficientnet-b0-v1.0"
}
```
*Grade Mapping*:
- `0`: No DR (Non-referable)
- `1`: Mild DR (Non-referable in standard triage)
- `2`: Moderate DR (Referable)
- `3`: Severe DR (Referable)
- `4`: Proliferative DR (Urgent Referral)

#### D. Module 3: Lesion Segmentation (`segment_lesions`)
```json
{
  "lesions_detected": true,
  "mask_shape": [512, 512],
  "lesion_areas": {
    "hard_exudates_pixels": 1420,
    "hemorrhages_pixels": 890,
    "microaneurysms_pixels": 210,
    "cotton_wool_spots_pixels": 0
  },
  "lesion_mask_path": "/storage/cases/{case_id}/lesion_mask.png",
  "model_version": "unet-idrid-v1.0"
}
```

#### E. Module 4: Explainability & Calibration (`generate_gradcam`)
```json
{
  "gradcam_heatmap_path": "/storage/cases/{case_id}/gradcam.png",
  "overlay_image_path": "/storage/cases/{case_id}/gradcam_overlay.png",
  "target_class": 2,
  "calibrated_confidence": 0.784,
  "uncertainty_score": 0.142,
  "is_uncertain": false,
  "calibration_method": "temperature_scaling"
}
```

#### F. Unified Orchestration Response (`analyse_case`)
```json
{
  "case_id": "EYE-20261116-A1B2C3",
  "timestamp": "2026-11-16T16:50:00Z",
  "status": "completed",
  "quality": { ... },
  "classification": { ... },
  "segmentation": { ... },
  "explainability": { ... },
  "clinical_decision": {
    "referral_recommended": true,
    "urgency": "routine_referral",
    "rationale": "Moderate non-proliferative diabetic retinopathy detected with calibrated confidence 78.4%. Exudates present in macular region.",
    "action_required": "Referral to ophthalmologist within 4–6 weeks."
  },
  "disclaimer": "Research screening prototype only. Not a certified diagnostic medical device."
}
```

---

## 3. Backend API Architecture & Proposed Endpoint Specifications

### 3.1 Proposed API Versioning & Endpoints
All endpoints are organized under the `/api/v1` namespace.

| Method | Endpoint | Description | Request Payload | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Service liveness, readiness, DB connection probe | None | `HealthResponse` |
| `POST` | `/api/v1/screenings` | Upload fundus image and initiate screening pipeline | `multipart/form-data` (file, metadata) | `ScreeningInitiatedResponse` (202) or `ScreeningResponse` (200) |
| `GET` | `/api/v1/screenings/{id}` | Retrieve screening result by screening ID | None | `ScreeningDetailResponse` |
| `GET` | `/api/v1/screenings/{id}/report`| Get generated structured screening report | None | `ScreeningReportResponse` (JSON/HTML/PDF) |
| `GET` | `/api/v1/screenings/{id}/explanation` | Fetch Grad-CAM heatmap and lesion overlays | None | `ExplanationResponse` |

### 3.2 Pydantic V2 Schema Hierarchy Plan
```
backend/app/schemas/
├── common.py           # Standard API response envelope, ErrorDetail
├── health.py           # HealthResponse, ServiceStatus
├── screening.py        # ScreeningCreate, ScreeningResponse, ScreeningDetailResponse
├── prediction.py       # GradePrediction, ProbabilityDistribution, QualityMetrics
└── explanation.py      # GradCAMDetails, CalibrationDetails, LesionSegmentationDetails
```

### 3.3 Database Schema & Persistence Architecture
- **Table `screening_records`**:
  - `id`: Integer (Primary Key)
  - `case_id`: String(64) (Unique, Indexed)
  - `patient_identifier`: String(64) (Salted hash, never plain PII)
  - `image_path`: String(256)
  - `status`: String(32) (`pending`, `processing`, `completed`, `failed`, `rejected_quality`)
  - `quality_gradable`: Boolean
  - `overall_quality_score`: Float
  - `predicted_grade`: Integer (0–4)
  - `calibrated_confidence`: Float
  - `uncertainty_score`: Float
  - `referable`: Boolean
  - `urgency`: String(32)
  - `model_version`: String(64)
  - `execution_time_ms`: Integer
  - `created_at`: DateTime(timezone=True)
  - `updated_at`: DateTime(timezone=True)

---

## 4. Frontend Architecture Audit & Component Roadmap

### 4.1 Component Tree Hierarchy

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Navbar.jsx               # Navigation bar with branding & system status
│   │   ├── Footer.jsx               # Medical disclaimer & version info
│   │   └── AppLayout.jsx            # Main view wrapper
│   ├── screening/
│   │   ├── ImageDropzone.jsx        # Drag-and-drop retinal fundus upload with validation
│   │   ├── UploadProgress.jsx       # Real-time processing progress indicator
│   │   └── QualityWarningModal.jsx  # Immediate alert for poor quality/ungradable images
│   ├── results/
│   │   ├── DRGradeCard.jsx          # Visual 0–4 severity indicator with badge styling
│   │   ├── ConfidenceGauge.jsx      # Calibrated confidence & uncertainty visualization
│   │   ├── ReferralBanner.jsx       # Clear color-coded clinical escalation recommendation
│   │   └── LesionSummaryTable.jsx   # Tabular summary of segmented lesion areas
│   ├── visualization/
│   │   ├── ImageViewer.jsx          # Dual-pane comparison viewer (Original vs Heatmap)
│   │   ├── GradCAMOverlay.jsx       # Interactive opacity slider for Grad-CAM overlay
│   │   └── LesionMaskViewer.jsx     # Toggle layers for exudates/hemorrhages/MAs
│   └── reports/
│       ├── ScreeningReportView.jsx  # Printable clinic summary report
│       └── DisclaimerBanner.jsx     # Prominent research disclaimer
├── pages/
│   ├── HomePage.jsx                 # System overview and entry point
│   ├── ScreeningPage.jsx            # Upload and live screening workspace
│   ├── ResultDetailPage.jsx         # Comprehensive patient case inspection
│   └── HistoryPage.jsx              # Searchable list of past screenings
└── services/
    ├── api.js                       # Base Axios/Fetch client with interceptors
    ├── screeningService.js          # API service for `/api/v1/screenings`
    └── reportService.js             # API service for report downloading
```

---

## 5. MATLAB & Simulink Integration Plan

### 5.1 MATLAB App Designer Integration
- **Protocol**: HTTP REST via `webread`/`webwrite` using `matlab/integration/api_connector.m`.
- **Contract**: Accepts fundus image path -> posts to `/api/v1/screenings` -> parses JSON response into MATLAB structs -> displays original, heatmap, and severity in App Designer UI components.
- **Fail-Safe**: If the API server is unreachable, `api_connector.m` returns structured error without crashing the desktop app.

### 5.2 Simulink Operational Workflow Simulation
- **Purpose**: Simulate patient arrival rates, screening queue depth, nurse-administered fundus photography, quality rejection recaptures, automated inference latency, and specialist referral wait times in rural health centers.
- **Engine**: SimEvents discrete-event simulation.
- **Scenario Definitions**:
  1. `normal_workflow.m`: Baseline 20 patients/day, 95% gradability, standard referral delay.
  2. `high_volume_scenario.m`: High-volume camp with 100 patients/day, resource bottlenecks.
  3. `poor_quality_scenario.m`: High ungradable rate (30%) simulating inexperienced operators, evaluating recapture queue congestion.

