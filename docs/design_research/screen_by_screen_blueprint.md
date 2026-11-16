# EYERIS — Screen-by-Screen UI/UX Design Blueprint
**Subsystem**: UI/UX Architecture & Screen Specifications  
**Role**: Senior Product Designer & Healthcare UX Architect (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 2026  
**Status**: Proposal for Design Approval Gate  

---

## Screen 1: Dashboard

### 1.1 Purpose & Primary Users
- **Purpose**: Serve as the operational mission control for the screening program, tracking daily screening throughput, identifying backlogged manual review cases, monitoring system health, and initiating new screenings.
- **Primary Users**: Screening Operators, Clinic Administrators, Reviewing Ophthalmologists.

### 1.2 Layout Wireframe (Text / ASCII Diagram)
```
+---------------------------------------------------------------------------------------------------------+
| [Header] Case Context: N/A | Status: 🟢 API Operational | DB: 🟢 Connected | Mode: Operator | User: Staff |
+---------------------------------------------------------------------------------------------------------+
| [Disclaimer] Research screening prototype (SIH PS26038). Not for primary diagnosis.                   |
+---------------------------------------------------------------------------------------------------------+
| [Quick Metrics Bar]                                                                                     |
| +--------------------+ +--------------------+ +--------------------+ +--------------------+             |
| | Total Screenings   | | Urgent Referrals   | | Pending Review     | | Quality Rejections |             |
| | 128                | | 14                 | | 6                  | | 3                  |             |
| | (Real DB count)    | | (Grades 3-4)       | | (Uncertain/Offline)| | (Quality < 0.60)   |             |
| +--------------------+ +--------------------+ +--------------------+ +--------------------+             |
+---------------------------------------------------------------------------------------------------------+
| [Main Grid: 2 Columns (70% Left / 30% Right)]                                                          |
|                                                                                                         |
| LEFT COLUMN: Recent Screening Activity Queue          | RIGHT COLUMN: Operational Telemetry             |
| +---------------------------------------------------+ | +---------------------------------------------+ |
| | [Search Case ID...] [Filter: All / Referrals]     | | | Quick Actions                               | |
| | +-----------------------------------------------+ | | | [ + Start New Screening ]                   | |
| | | Case ID   | Date/Time | Grade  | Urgency | Act| | | | [ View Pending Review Queue (6) ]           | |
| | | EYE-A1B2  | 10:42 AM  | Mod(2) | Routine |View| | | +---------------------------------------------+ |
| | | EYE-9F40  | 10:15 AM  | PDR(4) | URGENT  |View| | | AI Model Availability Subsystems              | |
| | | EYE-3C81  | 09:50 AM  | Ungrad | RECAPTURE|View | | | - Quality Model:   🟢 Active (Heuristic)   | |
| | +-----------------------------------------------+ | | | - DR Classifier:   🟡 Offline (Safe Fallback)| |
| | (Direct link to full Screening History)           | | | - Segmentation:    🟡 Offline (Safe Fallback)| |
| +---------------------------------------------------+ | | - Explainability:  🟡 Offline (Safe Fallback)| |
|                                                       | +---------------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

### 1.3 Telemetry Data Integrity Rules
- **Genuine Available Metrics**: Total records count, urgent cases tally, ungradable/recapture tally, and pending review tally derived directly from `/api/v1/screenings`.
- **Unavailable Metrics**: Population prevalence rates, sensitivity/specificity percentages, and multi-center clinical analytics remain marked as `"Analytics Uncalibrated — Prototype Mode"` until validated epidemiological data is loaded. No fictitious metrics are displayed.

---

## Screen 2: New Screening (Intake & Quality Gate)

### 2.1 Purpose & Primary Users
- **Purpose**: High-throughput retinal photograph intake, patient metadata association (pseudonymous hash and bilateral eye tag), client-side file validation, and instant quality feedback.
- **Primary Users**: Screening Operators, Community Outreach Nurses.

### 2.2 Layout Wireframe
```
+---------------------------------------------------------------------------------------------------------+
| [Navbar] EYERIS > New Screening Intake                                                                  |
+---------------------------------------------------------------------------------------------------------+
| [Form Container: Centered Max Width 800px]                                                              |
|                                                                                                         |
| 1. Examination Metadata                                                                                 |
| +---------------------------------------------------+ +-----------------------------------------------+ |
| | Patient Identifier / EHR Hash                     | | Eye Selection (Required)                      | |
| | [ PATIENT-8942-X                                ] | | [ (•) Right Eye (OD)   ( ) Left Eye (OS)    ] | |
| +---------------------------------------------------+ +-----------------------------------------------+ |
|                                                                                                         |
| 2. Retinal Fundus Photograph Intake                                                                     |
| +-----------------------------------------------------------------------------------------------------+ |
| |                                                                                                     | |
| |                                 [ 📷 Drag & Drop Retinal Image ]                                    | |
| |                                                                                                     | |
| |                       Select high-resolution color fundus photograph (JPEG / PNG)                   | |
| |                       Maximum file size: 15 MB | Minimum resolution: 512 x 512 px                  | |
| |                                                                                                     | |
| |                                      [ Browse Local File ]                                          | |
| |                                                                                                     | |
| +-----------------------------------------------------------------------------------------------------+ |
|                                                                                                         |
| 3. Pre-Upload Preview & Validation Card (Revealed upon selection)                                        |
| +-----------------------------------------------------------------------------------------------------+ |
| | [Thumbnail 120x120] | File: fundus_OD_001.jpg | Size: 3.4 MB | Dimensions: 2048 x 1536 px (PASS)     | |
| | [Status Pill: Ready to Upload]                                              [ 🗑 Remove File ]      | |
| +-----------------------------------------------------------------------------------------------------+ |
|                                                                                                         |
| [ Actions: [ Cancel ]                            [ ⚡ Upload & Execute Screening Analysis ] ]           |
+---------------------------------------------------------------------------------------------------------+
```

### 2.3 Validation & Error Handling
- **Client Validation**: Verifies MIME type (`image/jpeg`, `image/png`) and file size ($\le 15$ MB). If file is $>15$ MB, button disables and a red banner states: *"File exceeds 15 MB maximum limit"*.
- **Quality Rejection Handling**: If the backend quality score is $<0.60$, the view does not advance to results. Instead, an amber modal appears:
  - Header: *"Image Ungradable — Recapture Recommended"*
  - Specific reason: *"Severe corneal reflection / blur detected in macular field."*
  - Action button: *"Recapture Retinal Photograph"* (returns operator to fresh upload state immediately).

---

## Screen 3: Screening History (Triage Registry)

### 3.1 Purpose & Primary Users
- **Purpose**: Searchable, filterable audit registry of all processed screenings, enabling clinicians to locate historical cases, export registries, and triage backlogged patients.
- **Primary Users**: Ophthalmologists, Clinic Administrators.

### 3.2 Layout Wireframe
```
+---------------------------------------------------------------------------------------------------------+
| [Header] Screening History Registry (128 Total Screenings)                       [ 📥 Export CSV ]       |
+---------------------------------------------------------------------------------------------------------+
| [Filter Toolbar]                                                                                        |
| [ 🔍 Search Case ID or Patient Hash... ]  [ Status: All ▼ ]  [ Urgency: All ▼ ]  [ Sort: Newest First ▼]|
+---------------------------------------------------------------------------------------------------------+
| [High-Density Data Table]                                                                               |
| +-------------+------------------+-----+----------+-----------+--------------------+------------------+ |
| | Case ID     | Screening Date   | Eye | Quality  | DR Grade  | Referral Urgency   | Action           | |
| +-------------+------------------+-----+----------+-----------+--------------------+------------------+ |
| | EYE-9F4081  | Nov 16, 10:15 AM | OD  | 0.94 P   | Grade 4   | 🔴 URGENT REFERRAL | [ Open Analysis ]| |
| | EYE-A1B290  | Nov 16, 10:42 AM | OS  | 0.88 P   | Grade 2   | 🟡 ROUTINE REFERRAL| [ Open Analysis ]| |
| | EYE-5E2104  | Nov 16, 09:12 AM | OD  | 0.92 P   | Grade 0   | 🟢 ANNUAL SCREEN   | [ Open Analysis ]| |
| | EYE-3C8144  | Nov 16, 08:50 AM | OS  | 0.42 F   | Ungraded  | 🔴 RECAPTURE REQ   | [ Open Analysis ]| |
| | EYE-7B1990  | Nov 15, 04:30 PM | OD  | 0.85 P   | Pending   | 🟣 MANUAL REVIEW   | [ Open Analysis ]| |
| +-------------+------------------+-----+----------+-----------+--------------------+------------------+ |
| [Pagination: Showing 1 - 25 of 128 cases]                       [ < Previous ] [ 1 ] [ 2 ] [ Next > ]   |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 4: Screening Details (Clinical Analysis Workspace)

### 4.1 Purpose & Primary Users
- **Purpose**: Dedicated, high-precision retinal analysis workspace providing clinicians with true-color anatomical fundus photography, Grad-CAM class activation overlays, and U-Net lesion segmentation.
- **Primary Users**: Consulting Ophthalmologists, Retina Specialists.

### 4.2 Layout Wireframe (Desktop Workspace: 60% Viewer / 40% Triage Telemetry)
```
+---------------------------------------------------------------------------------------------------------+
| [Top Bar] Case ID: EYE-9F4081 | Patient: #8942-X | Eye: Right (OD) | Date: 16-Nov-2026 | [ 🖨 View Report ]|
+---------------------------------------------------------------------------------------------------------+
| [Triage Banner: 🔴 URGENT SPECIALIST REFERRAL RECOMMENDED — High Risk of Vision Loss (PDR detected)]     |
+---------------------------------------------------+-----------------------------------------------------+
| LEFT PANE: Retinal Fundus Viewport (60% Width)    | RIGHT PANE: Diagnostic Telemetry (40% Width)        |
|                                                   |                                                     |
| [Viewport Toolbar]                                | 1. DR Classification (ICDR 0–4)                     |
| Layer: [ (•) Grad-CAM  ( ) Lesions  ( ) Raw ]     | +-------------------------------------------------+ |
| Opacity: [----●----------] 65%   [ 🔍 Zoom ] [ ⟲ ]| | Grade 4 — Proliferative Diabetic Retinopathy    | |
|                                                   | | [ 0: None | 1: Mild | 2: Mod | 3: Sev | 4: PDR ] | |
| +-----------------------------------------------+ | | Active segment: [ 4: PDR (Crimson Red) ]        | |
| |                                               | | +-------------------------------------------------+ |
| |                                               | |                                                     |
| |                                               | | 2. Calibrated Confidence & Uncertainty            |
| |             [ RETINAL FUNDUS CANVAS ]         | | +-------------------------------------------------+ |
| |             Synchronized Pan & Zoom           | | | Calibrated Probability: 91.4%                   | |
| |             Interactive Heatmap Blend         | | | Epistemic Uncertainty:  0.08 (Low / Confident)  | |
| |             Anatomical Landmark Preservation  | | | [ Progress Bar: 91.4% ]                         | |
| |                                               | | +-------------------------------------------------+ |
| |                                               | |                                                     |
| +-----------------------------------------------+ | 3. Retinal Lesion Quantification (U-Net)           |
| (Shortcut: Hold Spacebar to reveal raw fundus)    | +-------------------------------------------------+ |
|                                                   | | [X] Neovascularization:  140 px detected        | |
|                                                   | | [X] Blot Hemorrhages:    780 px detected        | |
|                                                   | | [X] Hard Exudates:       420 px detected        | |
|                                                   | +-------------------------------------------------+ |
|                                                   |                                                     |
|                                                   | 4. Technical Quality Assessment                     |
|                                                   | Quality: 0.94 / 1.00 (Gradable: YES)                |
|                                                   | Sharpness: 0.92 | Illumination: 0.95 | Contrast: 0.9|
+---------------------------------------------------+-----------------------------------------------------+
```

### 4.3 Mandatory Clinical Safety Rules
- **Grad-CAM Caution**: UI disclaimer reads: *"Attention heatmaps reflect model activation density and do not establish direct anatomical causality."*
- **Ungradable Image Rejection**: If `is_gradable` is False, the DR Grade panel is disabled and locked to `"Ungraded — Inadequate Quality"`, strictly preventing false reassurance.

---

## Screen 5: Reports (Printable Clinical Summary)

### 5.1 Purpose & Primary Users
- **Purpose**: Provide a formal, tamper-evident physical and digital medical summary for patient handoff, EHR archival, and ophthalmologist counter-signature.
- **Primary Users**: Reviewing Ophthalmologists, Primary Care Physicians, Patients.

### 5.2 Layout Wireframe
```
+---------------------------------------------------------------------------------------------------------+
| [Toolbar: Screen Only]  [ ← Back to Analysis ]                         [ 🖨 Print / Export to PDF ]      |
+---------------------------------------------------------------------------------------------------------+
| [PRINTABLE CLINICAL REPORT CONTAINER - White Background, Black Text, Standard A4 Geometry]               |
|                                                                                                         |
|  =====================================================================================================  |
|  EYERIS RETINAL SCREENING REPORT                                             Clinic: Rural Health Camp 4|
|  SIH Problem Statement PS26038                                               Exam Date: 16-Nov-2026     |
|  =====================================================================================================  |
|                                                                                                         |
|  PATIENT & EXAM IDENTIFIERS:                                                                            |
|  - Case ID: EYE-9F4081-OD          - Patient Ref: HASH-8942-X           - Examined Eye: Right (OD)     |
|                                                                                                         |
|  CLINICAL FINDINGS & TRIAGE RECOMMENDATION:                                                             |
|  -----------------------------------------------------------------------------------------------------  |
|  - DR Severity Staging:    GRADE 4 — PROLIFERATIVE DIABETIC RETINOPATHY (PDR)                           |
|  - Calibrated Confidence:  91.4%                                                                        |
|  - Referral Status:        REFERRAL MANDATORY                                                           |
|  - Escalation Urgency:     URGENT SPECIALIST REFERRAL (Within 1–2 Weeks)                                |
|  - Clinician Guidance:     High risk of severe vision loss. Immediate dilated ophthalmoscopic           |
|                            evaluation and consideration for panretinal photocoagulation (PRP).          |
|                                                                                                         |
|  IMAGE QUALITY ASSESSMENT:                                                                              |
|  - Overall Quality: PASS (0.94 / 1.00) | Sharpness: 0.92 | Illumination: 0.95 | Contrast: 0.94          |
|                                                                                                         |
|  RETINAL IMAGERY:                                                                                       |
|  +-------------------------------------+  +-------------------------------------+                       |
|  | [Thumbnail: Preprocessed Fundus]    |  | [Thumbnail: Grad-CAM Saliency Map]  |                       |
|  +-------------------------------------+  +-------------------------------------+                       |
|                                                                                                         |
|  OPHTHALMOLOGIST REVIEW & SIGN-OFF:                                                                     |
|  Reviewing Clinician: ___________________________    License / Reg No: _____________________________    |
|  Clinical Action Taken: [ ] Referred   [ ] Monitored   Signature / Date: ___________________________    |
|                                                                                                         |
|  IMPORTANT MEDICAL DISCLAIMER:                                                                          |
|  Generated by EYERIS research prototype. Not an autonomous diagnostic device. Confirmation required.   |
|  =====================================================================================================  |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 6: System & Model Status

### 6.1 Purpose & Primary Users
- **Purpose**: Real-time diagnostic telemetry on all backend services, database connections, and ML model subsystems.
- **Primary Users**: Technical Leads, System Administrators, SIH Evaluators.

### 6.2 Layout Wireframe
```
+---------------------------------------------------------------------------------------------------------+
| [Header] System Diagnostics & Subsystem Pipeline Telemetry                                              |
+---------------------------------------------------------------------------------------------------------+
| Core Infrastructure Status                                                                              |
| +-------------------------------+ +-------------------------------+ +---------------------------------+ |
| | FastAPI REST Gateway          | | PostgreSQL Metadata DB        | | Local Image Storage             | |
| | 🟢 Status: Operational (200)   | | 🟢 Status: Connected (pool:5) | | 🟢 Status: Writable             | |
| | Version: 0.1.0                | | Latency: 2.1 ms               | | Free Space: 142 GB              | |
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

