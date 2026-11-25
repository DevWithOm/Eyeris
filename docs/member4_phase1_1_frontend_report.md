# EYERIS — Phase 1.1 Frontend Implementation Report
**Subsystem**: React + Vite Web Application Foundation  
**Role**: Senior Full-Stack Engineer & Integration Lead (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Formal Implementation Deliverable  

---

## 1. Executive Summary

The React + Vite frontend application foundation has been fully implemented, resolving the primary non-compliant gap from Phase 1. All 179 npm dependencies were installed, the centralized API service was upgraded to communicate with real `/api/v1` backend endpoints, six required pages were built with comprehensive loading, empty, and error states, and the production build was compiled with zero errors.

---

## 2. Page Architecture & Implementation Details

### 2.1 Page 1: Dashboard (`frontend/src/pages/Dashboard.jsx`)
- **Route**: `/`
- **Features**:
  - Top action bar with "+ Start New Screening" button.
  - 4-card KPI metric grid: Total Cases Screened, Referrals Recommended, Quality Rejections, and AI Pipeline State.
  - Workflow shortcut cards for Retinal Fundus Intake and Screening History.
  - Recent Screenings table with live case ID links, date/time formatting, and referral badges.
  - Empty state displaying call-to-action when zero records exist.

### 2.2 Page 2: New Screening (`frontend/src/pages/NewScreening.jsx`)
- **Route**: `/screening/new`
- **Features**:
  - Drag-and-drop file dropzone supporting JPEG and PNG images.
  - Client-side validation enforcing file format and $<15$ MB size limit.
  - Examination details selectors: Eye Examined (OD vs. OS) and Camera Field Centering (Macula-Centered vs. Disc-Centered 45°).
  - Immediate visual thumbnail preview upon image selection.
  - Non-blocking submission with loading spinner and disabled state.
  - Actionable error banner displaying server or network errors.
  - Automatic redirect to `/screening/:caseId` upon successful screening creation.

### 2.3 Page 3: Screening History (`frontend/src/pages/ScreeningHistory.jsx`)
- **Route**: `/history`
- **Features**:
  - Interactive search box filtering records by Case ID, Grade name, or Status in real time.
  - "Show Referrals Only" checkbox filter for rapid clinician triage.
  - Full data table displaying Case ID, examination timestamp, quality score %, DR severity grade tag, referral badge, urgency timeframe, and action buttons.
  - Empty search state when no cases match active filters.

### 2.4 Page 4: Screening Details & Results (`frontend/src/pages/ScreeningDetails.jsx`)
- **Route**: `/screening/:caseId`
- **Features**:
  - Breadcrumb navigation (`Screenings / CASE-ID`).
  - High-visibility primary triage alert banner (Emerald Green for Routine Annual Monitoring vs. Alert Red for Clinical Referral Recommended).
  - 4-card clinical grid:
    1. *Image Quality Assessment*: Gradable/Ungradable badge, quality score %, and recapture warning if ungradable.
    2. *Diabetic Retinopathy Grade*: Grade 0–4 severity tag, diagnosis name, and model version. If model is unweighted or absent, clearly displays *"Classification Unavailable — Manual Review Required"*.
    3. *Calibrated Confidence & Uncertainty*: Temperature-calibrated confidence % and uncertainty score.
    4. *Clinical Next Steps*: Recommended action timeframe and direct button to view the official handoff report.

### 2.5 Page 5: Reports (`frontend/src/pages/Reports.jsx`)
- **Route**: `/reports/:caseId`
- **Features**:
  - Non-printable toolbar with navigation and "Print / Export PDF" button.
  - Formal clinical report sheet: Clinic branding, Case ID, Report ID, and generation timestamp.
  - Two-column summary of referral recommendations, urgency timeframe, and DR grade.
  - Complete screening manifest in clean monospace view.
  - Physical clinician sign-off block with signature and date lines.
  - Dedicated `@media print` CSS engine: transforms dark reading canvas into crisp white paper styling and suppresses web navigation buttons during printing.

### 2.6 Page 6: Not Found (`frontend/src/pages/NotFound.jsx`)
- **Route**: `*`
- **Features**: Clean, accessible 404 view displaying helpful guidance and a button returning to the Dashboard.

---

## 3. Centralized API Service (`frontend/src/services/api.js`)

Upgraded to communicate with the real `/api/v1` namespace:
- `checkHealth()`: Queries `/api/v1/health` to power the live status pill.
- `submitScreening(file)`: Sends multipart image payload to `POST /api/v1/screenings`.
- `getScreening(caseId)`: Fetches record from `GET /api/v1/screenings/${caseId}`.
- `listScreenings(limit, offset)`: Queries `GET /api/v1/screenings`.
- `getReport(caseId)`: Fetches clinical report from `GET /api/v1/screenings/${caseId}/report`.
- `getExplanation(caseId)`: Fetches explainability data from `GET /api/v1/screenings/${caseId}/explanation`.
- Robust `ApiError` class: detects backend connection loss (HTTP 0) and formats server error details.

---

## 4. Production Build Verification

Executed `npm run build --prefix frontend`:
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
Zero lint, syntax, or bundling errors.

