# EYERIS — Screen-by-Screen UI/UX Design Blueprint (Revision 1)
**Subsystem**: UI/UX Architecture & Screen Specifications  
**Role**: Senior Product Designer & Healthcare UX Architect (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 16, 2026  
**Status**: Revised Specification Incorporating Member 4 Approved Design Decisions  

---

## 1. Member 4 Approved Design Decisions

This revised screen blueprint incorporates the following core governance rules:
1. **Primary Technical Showcase**: Designates **Screen 4: Screening Details (Retinal Image Analysis Workspace)** as the primary technical and clinical centerpiece of the system.
2. **Wireframe Value Labeling**: Removes all unannotated numerical figures that could be mistaken for live clinical results. All figures are explicitly labeled as `[Example Wireframe Value: e.g. N]` or `[Example Schema Value]`.
3. **Provisional Engineering Values**: Quality threshold `0.60` and uncertainty threshold `0.35` are explicitly designated as configurable engineering parameters awaiting clinical dataset calibration.
4. **Causality Guardrail**: The retinal workspace includes an obligatory notice: *"Class activation heatmaps visualize deep network feature correlations and do not demonstrate anatomical lesion causality."*
5. **Architectural Separation of States**: Fully decouples:
   - *Model Unavailability* (`status: "pending_review"`, manual clinical assessment required).
   - *Quality Failure* (`is_gradable: false`, recapture mandatory, classification aborted).
   - *Model Uncertainty* (`uncertainty_detected: true`, specialist review gate).
   - *Clinical Referral* (ICDR stage-based clinical guidance: routine, prompt, urgent).
6. **Role-Aware Presentation Layer**: Operator Mode and Specialist Mode share the exact same underlying pipeline API and decision payload; they represent presentation-only view toggles.
7. **Accessible Fundus Inspection**: The raw, true-color fundus photograph is guaranteed to be accessible at all times via opacity sliders ($0–100\%$), dual-pane comparison, and spacebar reveal.
8. **Multi-Channel Accessibility**: Color is never the sole indicator; every state has an icon, text, and numeric level.

---

## Screen 1: Dashboard

### 1.1 Purpose & Primary Users
- **Purpose**: Operational control center tracking genuine screening counts from the database, pending manual reviews, quality failure rates, and system telemetry.
- **Primary Users**: Screening Operators, Clinic Administrators, Reviewing Ophthalmologists.

### 1.2 Layout Wireframe
*(Note: All wireframe numbers are illustrative schema mockups and do not represent actual patient data).*

```
+---------------------------------------------------------------------------------------------------------+
| [Header] EYERIS Screening | Status: 🟢 API Operational | DB: 🟢 Connected | Mode: Operator | User: Staff |
+---------------------------------------------------------------------------------------------------------+
| [Disclaimer] Research screening prototype (SIH PS26038). Not for primary diagnosis.                   |
+---------------------------------------------------------------------------------------------------------+
| [Quick Operational Telemetry Bar - Derived Strictly from Database Records]                              |
| +--------------------+ +--------------------+ +--------------------+ +--------------------+             |
| | Total Screenings   | | Urgent Referrals   | | Pending Review     | | Quality Rejections |             |
| | [Ex: e.g. 128]     | | [Ex: e.g. 14]      | | [Ex: e.g. 6]       | | [Ex: e.g. 3]       |             |
| | (Real DB count)    | | (Grades 3-4)       | | (Uncertain/Offline)| | (Quality < 0.60)   |             |
| +--------------------+ +--------------------+ +--------------------+ +--------------------+             |
+---------------------------------------------------------------------------------------------------------+
| [Operations Grid: 2 Columns (70% Left / 30% Right)]                                                     |
|                                                                                                         |
| LEFT COLUMN (70%): Recent Screening Activity Queue    | RIGHT COLUMN (30%): Telemetry & Actions         |
| +---------------------------------------------------+ | +---------------------------------------------+ |
| | [Search Case ID...] [Filter: All / Referrals]     | | | Quick Actions:                              | |
| | +-----------------------------------------------+ | | | [ + Start New Screening ]                   | |
| | | Case ID   | Exam Date | Grade   | Urgency| Act| | | | [ View Pending Review Queue ([Ex: e.g. 6]) ] | |
| | | EYE-A1B2  | Today     | Mod [2] | Routine|View| | | +---------------------------------------------+ |
| | | EYE-9F40  | Today     | PDR [4] | URGENT |View| | | AI Model Availability Subsystems:             | |
| | | EYE-3C81  | Today     | Ungrad  | RECAP  |View| | | - Quality Check:  🟢 Operational (Heuristic) | |
| | +-----------------------------------------------+ | | | - DR Classifier:  🟡 Offline (Safe Fallback)| |
| | (Link to full Screening History Registry)         | | | - Segmentation:   🟡 Offline (Safe Fallback)| |
| +---------------------------------------------------+ | | - Explainability: 🟡 Offline (Safe Fallback)| |
|                                                       | +---------------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 2: New Screening (Intake & Quality Gate)

### 2.1 Purpose & Primary Users
- **Purpose**: Rapid, fail-safe retinal image intake, patient pseudonymous token assignment, bilateral eye selection (OD/OS), pre-upload file validation, and instant in-chair quality check.
- **Primary Users**: Screening Operators, Community Outreach Nurses.

### 2.2 Layout Wireframe
```
+---------------------------------------------------------------------------------------------------------+
| [Navbar] EYERIS > New Screening Intake                                                                  |
+---------------------------------------------------------------------------------------------------------+
| [Intake Container: Centered Max Width 800px]                                                            |
|                                                                                                         |
| 1. Examination Metadata:                                                                                |
| +---------------------------------------------------+ +-----------------------------------------------+ |
| | Patient Identifier / EHR Token (Required)         | | Examined Eye Selection (Required)             | |
| | [ PATIENT-EX-8942                               ] | | [ (•) Right Eye (OD)   ( ) Left Eye (OS)    ] | |
| +---------------------------------------------------+ +-----------------------------------------------+ |
|                                                                                                         |
| 2. Retinal Fundus Photograph Intake Dropzone:                                                           |
| +-----------------------------------------------------------------------------------------------------+ |
| |                                                                                                     | |
| |                                 [ 📷 Drag & Drop Retinal Fundus Image ]                             | |
| |                                                                                                     | |
| |                       Supported formats: JPEG, PNG | Maximum file size: 15 MB                       | |
| |                       Minimum recommended resolution: 512 x 512 pixels                              | |
| |                                                                                                     | |
| |                                      [ Select Local File ]                                          | |
| |                                                                                                     | |
| +-----------------------------------------------------------------------------------------------------+ |
|                                                                                                         |
| 3. Pre-Upload File Validation (Appears upon file selection):                                            |
| +-----------------------------------------------------------------------------------------------------+ |
| | [Thumbnail 100x100] | File: fundus_OD_001.jpg | Size: 3.4 MB | Dimensions: 2048 x 1536 px (PASS)     | |
| | Status: Validated & Ready for Intake                                        [ 🗑 Remove File ]      | |
| +-----------------------------------------------------------------------------------------------------+ |
|                                                                                                         |
| [ Actions: [ Cancel ]                            [ ⚡ Upload & Execute Screening Analysis ] ]           |
+---------------------------------------------------------------------------------------------------------+
```

### 2.3 Instant Quality Rejection Handling (State B)
If the backend quality evaluation yields `overall_quality_score < 0.60` (provisional engineering threshold) or `is_gradable == False`:
- Downstream deep classification is aborted to prevent misleading reassurance.
- An amber **Quality Warning Modal** appears:
  - Header: `[⚠] Image Quality Insufficient for Automated Screening`
  - Cause: `Severe blur / corneal reflection detected in macular field.`
  - Action: `[ Recapture Retinal Photograph ]` (Resets the dropzone while the patient is still seated).

---

## Screen 3: Screening History (Triage Registry)

### 3.1 Purpose & Primary Users
- **Purpose**: Searchable, filterable audit registry of all screening records, supporting clinical audits, quality checks, and cohort tracking.
- **Primary Users**: Ophthalmologists, Clinic Administrators.

### 3.2 Layout Wireframe
*(Note: Table values are illustrative schema mockups).*

```
+---------------------------------------------------------------------------------------------------------+
| [Header] Screening History Registry ([Example Total: e.g. 128])                  [ 📥 Export CSV ]       |
+---------------------------------------------------------------------------------------------------------+
| [Filter Bar]                                                                                            |
| [ 🔍 Search Case ID or Token... ] [ Status: All ▼ ] [ Urgency: All ▼ ] [ Eye: All ▼ ] [ Sort: Date ▼ ]  |
+---------------------------------------------------------------------------------------------------------+
| [High-Density Data Table]                                                                               |
| +-------------+------------------+-----+----------+-----------+--------------------+------------------+ |
| | Case ID     | Screening Date   | Eye | Quality  | DR Grade  | Referral Urgency   | Action           | |
| +-------------+------------------+-----+----------+-----------+--------------------+------------------+ |
| | EYE-9F4081  | [Ex: 16-Nov-26]  | OD  | [Ex:0.94]| [Ex: G4]  | 🔴 [⯄] URGENT REF  | [ Open Analysis ]| |
| | EYE-A1B290  | [Ex: 16-Nov-26]  | OS  | [Ex:0.88]| [Ex: G2]  | 🟡 [◆] ROUTINE REF | [ Open Analysis ]| |
| | EYE-5E2104  | [Ex: 16-Nov-26]  | OD  | [Ex:0.92]| [Ex: G0]  | 🟢 [●] ANNUAL MON  | [ Open Analysis ]| |
| | EYE-3C8144  | [Ex: 16-Nov-26]  | OS  | [Ex:0.42]| Ungraded  | 🔴 [⚠] RECAPTURE   | [ Open Analysis ]| |
| | EYE-7B1990  | [Ex: 15-Nov-26]  | OD  | [Ex:0.85]| Pending   | 🟣 [⏸] MANUAL REV  | [ Open Analysis ]| |
| +-------------+------------------+-----+----------+-----------+--------------------+------------------+ |
| [Pagination: Showing 1 - 25 of 128 records]                     [ < Previous ] [ 1 ] [ 2 ] [ Next > ]   |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 4: Screening Details — Retinal Image Analysis Workspace (PRIMARY TECHNICAL SHOWCASE)

### 4.1 Purpose & Primary Users
- **Purpose**: Serve as the flagship technical and clinical centerpiece of EYERIS. Provides dual-pane synchronized retinal inspection, interactive Grad-CAM heatmap opacity blending, U-Net lesion segmentation overlays, and calibrated uncertainty metrics.
- **Primary Users**: Consulting Ophthalmologists, Retina Specialists.

### 4.2 Layout Wireframe (60% Retinal Canvas / 40% Clinical Telemetry)
*(All numerical metrics are labeled illustrative examples).*

```
+---------------------------------------------------------------------------------------------------------+
| [Top Bar] Case ID: EYE-9F4081 | Patient: #EX-8942 | Eye: Right (OD) | Date: 16-Nov-2026 | [ 🖨 Report ]   |
+---------------------------------------------------------------------------------------------------------+
| [Triage Banner: 🔴 [⯄] URGENT REFERRAL RECOMMENDED — Vision-Threatening Retinopathy Suspected]          |
+---------------------------------------------------+-----------------------------------------------------+
| LEFT PANE: Retinal Fundus Viewport (60% Width)    | RIGHT PANE: Diagnostic Telemetry (40% Width)        |
|                                                   |                                                     |
| [Viewport Toolbar: Height 42px]                   | 1. DR Disease Severity Staging (ICDR 0–4)           |
| Layer: [ (•) Grad-CAM  ( ) Lesions  ( ) Raw ]     | +-------------------------------------------------+ |
| Opacity: [----●----------] [Ex: 65%]  [ 🔍 ] [ ⟲ ]| | [Example Staging: Grade 4 — Proliferative DR]   | |
| View: [ (•) Dual-Pane  ( ) Single Canvas ]        | | [ 0: None | 1: Mild | 2: Mod | 3: Sev | 4: PDR ]| |
|                                                   | | Active Segment: [ 4: PDR (Crimson Red) ]        | |
| +-----------------------------------------------+ | +-------------------------------------------------+ |
| |                                               | |                                                     |
| |             RETINAL FUNDUS CANVAS             | | 2. Calibrated Confidence & Epistemic Uncertainty  |
| |                                               | | +-------------------------------------------------+ |
| |         Synchronized Pan & Zoom Viewport      | | | Calibrated Probability: [Example: e.g. 91.4%]   | |
| |         Interactive Saliency Overlay          | | | Epistemic Uncertainty:  [Example: e.g. 0.08]    | |
| |         Anatomical Landmark Preservation      | | | Uncertainty Status:     [Low / Confident]       | |
| |                                               | | | (Provisional Alert Threshold: > 0.35)           | |
| |                                               | | +-------------------------------------------------+ |
| +-----------------------------------------------+ |                                                     |
| [Notice: Grad-CAM reflects activation density   | | 3. Retinal Lesion Quantification (U-Net)           |
| and does not establish anatomical causality]    | | +-------------------------------------------------+ |
| (Shortcut: Hold Spacebar to reveal raw fundus)    | | [X] Neovascularization: [Example: e.g. 140 px]  | |
|                                                   | | [X] Blot Hemorrhages:   [Example: e.g. 780 px]  | |
|                                                   | | [X] Hard Exudates:      [Example: e.g. 420 px]  | |
|                                                   | +-------------------------------------------------+ |
|                                                   |                                                     |
|                                                   | 4. Technical Quality Assessment                     |
|                                                   | Quality Score: [Example: e.g. 0.94] (Gradable: YES) |
|                                                   | Sharpness: [Ex: 0.92] | Illumination: [Ex: 0.95]    |
+---------------------------------------------------+-----------------------------------------------------+
```

---

## Screen 5: Reports (Printable Clinical Summary Sheet)

### 5.1 Purpose & Primary Users
- **Purpose**: Formal medical documentation summary engineered with pure CSS `@media print` rules for physical patient handoff, physical clinic filing, and ophthalmologist countersignature.
- **Primary Users**: Reviewing Ophthalmologists, Primary Care Physicians, Patients.

### 5.2 Layout Wireframe
*(Note: Example schema values labeled).*

```
+---------------------------------------------------------------------------------------------------------+
| [Toolbar: Screen Only]  [ ← Back to Analysis Workspace ]               [ 🖨 Print / Export to PDF ]     |
+---------------------------------------------------------------------------------------------------------+
| [PRINTABLE CLINICAL REPORT - A4 Geometry, Pure White Canvas, High-Contrast Black Typography]             |
|                                                                                                         |
|  =====================================================================================================  |
|  EYERIS RETINAL SCREENING REPORT                                             Clinic: Rural Health Camp 4|
|  SIH Problem Statement PS26038                                               Exam Date: 16-Nov-2026     |
|  =====================================================================================================  |
|                                                                                                         |
|  PATIENT & EXAMINATION IDENTIFIERS:                                                                     |
|  - Case ID: EYE-9F4081-OD          - Patient Ref: HASH-8942-X           - Examined Eye: Right (OD)     |
|                                                                                                         |
|  CLINICAL FINDINGS & REFERRAL RECOMMENDATION:                                                           |
|  -----------------------------------------------------------------------------------------------------  |
|  - Predicted Severity Staging: [Example: GRADE 4 — PROLIFERATIVE DIABETIC RETINOPATHY (PDR)]           |
|  - Calibrated Confidence:      [Example: e.g. 91.4%]                                                    |
|  - Clinical Referral Status:   REFERRAL RECOMMENDED                                                     |
|  - Escalation Urgency:         URGENT SPECIALIST REFERRAL (Within 1–2 Weeks)                            |
|  - Recommended Next Action:    Dilated retinal examination and consideration for retinal therapy.       |
|                                                                                                         |
|  IMAGE QUALITY ASSESSMENT:                                                                              |
|  - Technical Quality: PASS ([Example: 0.94 / 1.00]) | Sharpness: [Ex: 0.92] | Illumination: [Ex: 0.95]  |
|                                                                                                         |
|  RETINAL IMAGERY:                                                                                       |
|  +-------------------------------------+  +-------------------------------------+                       |
|  | [Thumbnail: Preprocessed Fundus]    |  | [Thumbnail: Grad-CAM Activation]    |                       |
|  +-------------------------------------+  +-------------------------------------+                       |
|                                                                                                         |
|  OPHTHALMOLOGIST REVIEW & COUNTERSIGNATURE:                                                             |
|  Reviewing Clinician: ___________________________    Registration / Reg No: ________________________    |
|  Action Confirmed: [ ] Referred  [ ] Monitored       Signature / Date: _____________________________    |
|                                                                                                         |
|  MANDATORY RESEARCH DISCLAIMER:                                                                         |
|  Generated by the EYERIS research screening prototype (SIH PS26038). Does not constitute an autonomous  |
|  definitive medical diagnosis. All findings must be confirmed by a licensed clinician.                 |
|  =====================================================================================================  |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 6: System & Model Status

### 6.1 Purpose & Primary Users
- **Purpose**: Real-time diagnostic telemetry probing core backend infrastructure and individual ML model pipeline subsystems.
- **Primary Users**: Technical Leads, System Administrators, Hackathon Judges.

### 6.2 Layout Wireframe
```
+---------------------------------------------------------------------------------------------------------+
| [Header] System Diagnostics & Subsystem Pipeline Telemetry                                              |
+---------------------------------------------------------------------------------------------------------+
| Core Service Infrastructure Status                                                                      |
| +-------------------------------+ +-------------------------------+ +---------------------------------+ |
| | FastAPI REST Gateway          | | PostgreSQL Metadata DB        | | Local Image Storage             | |
| | 🟢 Status: Operational (200)   | | 🟢 Status: Connected (pool:5) | | 🟢 Status: Writable             | |
| | Version: 0.1.0                | | Latency: [Ex: 2.1 ms]         | | Free Space: [Ex: 142 GB]        | |
| +-------------------------------+ +-------------------------------+ +---------------------------------+ |
|                                                                                                         |
| AI Model Subsystem Pipeline Status (Members 1, 2, 3 Integration)                                        |
| +-----------------------------------------------------------------------------------------------------+ |
| | Subsystem              | Member Responsibility | Active Check  | Model Architecture | Fallback Mode  | |
| +------------------------+-----------------------+---------------+--------------------+----------------+ |
| | 1. Quality Assessment  | Member 2 (Quality/Seg)| 🟢 Operational| Heuristic + Sharp  | Standard CV    | |
| | 2. DR Classification   | Member 1 (Classifier) | 🟡 Unharvested| EfficientNet-B0    | Safe Fallback  | |
| | 3. Lesion Segmentation | Member 2 (Quality/Seg)| 🟡 Unharvested| U-Net DR           | Mask Disabled  | |
| | 4. Explainability CAM  | Member 3 (Explain)    | 🟡 Unharvested| Grad-CAM / PyTorch | Safe Fallback  | |
| +------------------------+-----------------------+---------------+--------------------+----------------+ |
+---------------------------------------------------------------------------------------------------------+
```
