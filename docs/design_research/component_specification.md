# EYERIS — Reusable Component Specifications & Architecture
**Subsystem**: UI/UX Component Engineering  
**Role**: Senior Product Designer & Design Systems Engineer (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 2026  
**Status**: Proposal for Design Approval Gate  

---

## 1. Component Specification Framework

Every component in the EYERIS frontend follows a strict specification structure:
1. **Component Name & Location**: Path within `frontend/src/components/`.
2. **Reference Source & Observed Pattern**: Real-world commercial/clinical benchmark.
3. **EYERIS Adaptation & Justification**: How and why it was modified for retinal screening.
4. **Visual & Interaction States**: Default, Hover, Active, Focus, Disabled, Error, Loading.
5. **Accessibility Contract**: ARIA roles, keyboard interactions, contrast ratios.
6. **Implementation Priority**: Critical (Phase 1/2) vs Deferred (Phase 4).

---

## 2. Core Navigation & Layout Components

### 2.1 Global Patient Context Header (`Navbar.jsx`)
- **Reference**: NHS Digital Service Manual & Epic Hyperspace patient banner.
- **Observed Pattern**: Persistent top-bar displaying patient identifier, examination timestamp, and system status across all nested views.
- **EYERIS Adaptation**: Streamlined dark bar (`#090D16`) with active Case ID, connection health dot, active persona mode (Operator vs. Specialist), and user profile.
- **Implementation Priority**: **Critical (Already Foundationally Implemented)**.

### 2.2 Collapsible Sidebar (`Sidebar.jsx`)
- **Reference**: Linear Navigation & Vercel Dashboard.
- **Observed Pattern**: Slim 240px left sidebar collapsible to 64px icon rail with keyboard toggle (`Cmd/Ctrl + B`).
- **EYERIS Adaptation**: Dedicated navigation rail containing: Dashboard, New Screening, Screening History, System Status, and Settings. Includes keyboard accessibility navigation (`Tab` + `Enter`).
- **Implementation Priority**: **High (Phase 2)**.

### 2.3 Persistent Medical Disclaimer Banner (`DisclaimerBanner.jsx`)
- **Reference**: FDA De Novo Medical Device Labeling & Google Health ARDA.
- **Observed Pattern**: Mandatory visual notice identifying system as an investigational research decision-support tool.
- **EYERIS Adaptation**: Unobtrusive amber-toned bar (`rgba(245, 158, 11, 0.12)`) placed directly below top navigation. Never occludes diagnostic viewports.
- **Implementation Priority**: **Critical (Already Implemented)**.

---

## 3. Retinal Image Viewer Architecture (`DualImageViewer.jsx`)

### 3.1 Anatomical Viewport Architecture
```
+---------------------------------------------------------------------------------------------------------+
| [Viewport Toolbar: Height 42px]                                                                         |
| Layer: [ (•) Grad-CAM Heatmap  ( ) Lesion Masks  ( ) Raw Fundus ]                                       |
| Opacity: [----------●-----] 70% | Zoom: [ - ] 100% [ + ] | [ ⟲ Reset ] | [ ↔ Side-by-Side ]             |
+---------------------------------------------------+-----------------------------------------------------+
| PANE A: Reference Fundus (Preprocessed True-Color)| PANE B: AI Explainability Layer                     |
|                                                   |                                                     |
|                                                   |                                                     |
|             True-Color Fundus                     |             Grad-CAM Attention Heatmap              |
|             (Macula & Optic Disc)                 |             (Class 4 / Neovascularization)          |
|                                                   |             Overlaid with 70% Opacity               |
|                                                   |                                                     |
|                                                   |                                                     |
+---------------------------------------------------+-----------------------------------------------------+
| (Press-and-Hold Spacebar to momentarily reveal raw fundus photograph on Pane B)                         |
+---------------------------------------------------------------------------------------------------------+
```

### 3.2 Viewport Feature Prioritization Matrix

| Feature | Description | Implementation Priority | Technical Rationale |
| :--- | :--- | :---: | :--- |
| **Grad-CAM Opacity Slider** | HTML5 range slider ($0\% - 100\%$) controlling canvas alpha | **Critical (First Release)** | Eliminates diagnostic occlusion; allows clinician to verify underlying anatomy. |
| **Press-and-Hold Compare** | Holding Spacebar drops overlay opacity to 0% | **Critical (First Release)** | Enables instant visual flicker-comparison between AI map and real vessels. |
| **Synchronized Pan/Zoom** | Panning/zooming either pane updates both canvases | **High (Phase 2)** | Maintains exact anatomical cross-referencing between panes. |
| **Lesion Mask Toggles** | Independent checkboxes for exudates, hemorrhages, MAs | **High (Phase 2/3)** | Enables multi-task verification of segmentation outputs. |
| **Window/Level Contrast** | Radiologist-style contrast curve adjustments | **Deferred (Post-MVP)** | Not required for initial SIH prototype demonstration. |
| **Measurement Calipers** | Digital ruler measuring lesion millimeter diameter | **Deferred (Post-MVP)** | Requires physical camera sensor pixel calibration. |

---

## 4. Diagnostic & Telemetry Display Components

### 4.1 ICDR 5-Grade Severity Card (`DRGradeCard.jsx`)
- **Reference**: Thirona RetCAD & International Clinical DR Disease Severity Scale.
- **Observed Pattern**: Visual progression bar indicating severity tier from 0 (No DR) to 4 (Proliferative).
- **EYERIS Adaptation**: 5-segment horizontal segmented track with distinct color bands and active indicator caret. Displays grade number, formal ICDR label, and expandable softmax probability distribution.
- **States**:
  - *Normal / Grade 0*: Emerald Green (`#10B981`)
  - *Mild / Grade 1*: Cyan (`#06B6D4`)
  - *Moderate / Grade 2*: Warm Amber (`#F59E0B`)
  - *Severe / Grade 3*: Vibrant Orange (`#F97316`)
  - *Proliferative / Grade 4*: Crimson Red (`#EF4444`)
  - *Model Unavailable*: Muted Slate with `"Clinical Review Required"` badge.

### 4.2 Calibrated Confidence & Uncertainty Gauge (`ConfidenceGauge.jsx`)
- **Reference**: IBM Carbon Healthcare & Academic Uncertainty Quantification Standards.
- **Observed Pattern**: Precision progress bar showing calibrated probability alongside an epistemic uncertainty interval.
- **EYERIS Adaptation**: Dual-metric meter displaying temperature-scaled confidence ($0\% - 100\%$) and an explicit violet uncertainty band. Automatically flags cases exceeding uncertainty threshold ($>0.35$) with an "Escalate for Specialist Confirmation" badge.

### 4.3 Clinical Referral Banner (`ReferralBanner.jsx`)
- **Reference**: EyeArt & NHS Diabetic Eye Screening Programme (DESP).
- **Observed Pattern**: Explicit actionable referral recommendations with clinical urgency timeframes.
- **EYERIS Adaptation**: Color-coded alert banner with 5 distinct operational urgency tiers:
  1. `URGENT REFERRAL (1–2 Weeks)`: Proliferative DR (Grade 4). High risk of vitreous hemorrhage or tractional retinal detachment.
  2. `PROMPT REFERRAL (2–4 Weeks)`: Severe NPDR (Grade 3). High risk of progression.
  3. `ROUTINE REFERRAL (4–8 Weeks)`: Moderate NPDR (Grade 2). Referable DR.
  4. `ROUTINE ANNUAL SCREENING`: Mild (Grade 1) or Normal (Grade 0). Rescreen in 12 months.
  5. `MANDATORY RECAPTURE`: Ungradable image (Quality $<0.60$). Retake scan immediately.

---

## 5. Form & Intake Components

### 5.1 Retinal Image Dropzone (`ImageDropzone.jsx`)
- **Reference**: Stripe File Upload & LumineticsCore In-Chair Intake.
- **Observed Pattern**: Drag-and-drop area with immediate pre-validation feedback.
- **EYERIS Adaptation**: Form factor with 220px drop target, retinal camera icon, drag-hover glow, format validation (`image/jpeg`, `image/png`), 15MB file size limit, and instant pre-upload preview.

### 5.2 Bilateral Eye Selector (`EyeSelector.jsx`)
- **Reference**: Zeiss FORUM & Topcon Harmony PACS.
- **Observed Pattern**: Segmented pill switch toggling between Right Eye (OD - *Oculus Dexter*) and Left Eye (OS - *Oculus Sinister*).
- **EYERIS Adaptation**: High-contrast radio toggle matching standard ophthalmic charting conventions.

---

## 6. Defensive System States (Empty, Loading, Error)

### 6.1 Loading States (`SkeletonLoader.jsx`)
- **Design Rule**: Never display a blank screen or jarring layout shifts.
- **Implementation**: Muted pulse animation (`rgba(30, 41, 59, 0.5)`) mimicking the exact card geometries of the viewport, grade cards, and telemetry tables.

### 6.2 Empty States (`EmptyState.jsx`)
- **Design Rule**: Guide the user toward the next operational action.
- **Implementation**: Centered illustration icon (e.g. retinal scanner silhouette), clear title (*"No Screenings Found"*), descriptive guidance (*"Upload a fundus photograph to initiate an automated screening"*), and primary action button (*"Start New Screening"*).

### 6.3 Defensive Error Banners (`ErrorAlert.jsx`)
- **Design Rule**: Provide specific clinical/system cause and concrete recovery steps.
- **Implementation**: Left 4px border accent, warning icon, specific error message (e.g. *"FastAPI Backend Offline — Check localhost:8000"*), and a retry button.

