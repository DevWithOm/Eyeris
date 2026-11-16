# EYERIS — Medical AI UI/UX Design Comparison Matrix
**Subsystem**: UI/UX Research & Design Architecture  
**Role**: Senior Software Architect & Lead Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Formal Research Deliverable  

---

## 1. Multi-Dimensional Competitor Comparison Matrix

| System / Product | Image Quality UX & Gating | Explainability & Heatmap Layering | Diagnostic & Grading Granularity | Workflow Latency & Friction | Reading Room Ergonomics | Clinical Report Generation | Frontline Camp Suitability | Specialist Review Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Digital Diagnostics LumineticsCore (IDx-DR)** | **5/5** (Immediate in-chair retake alert) | **1/5** (Pure black box, zero visual explanation) | **2/5** (Binary mtmDR referral only) | **5/5** ($<30$s, minimal data entry) | **2/5** (High-glare light desktop client) | **3/5** (Standard EHR/billing summary) | **5/5** (Optimized for nurses & medical assistants) | **1/5** (Unacceptable for ophthalmologist verification) |
| **Eyenuk EyeArt** | **4/5** (Live capture feedback on camera) | **2/5** (Low explainability; basic lesion flags) | **3/5** (Binary mtmDR + vtDR/DME flags) | **4/5** ($<60$s cloud turnaround) | **3/5** (Standard web portal) | **4/5** (Comprehensive bilateral PDF report) | **4/5** (High adoption in primary care) | **2/5** (Specialists still require full manual rescreening) |
| **Google Health ARDA** | **5/5** (Real-time sharpness/exposure model) | **3/5** (Saliency maps in research deployments) | **4/5** (Full 5-class ICDR grading 0–4) | **5/5** (Engineered for thousands of patients/day) | **3/5** (Clean, responsive web view) | **3/5** (EHR-embedded summary) | **5/5** (Extensively validated in rural India & Thailand) | **3/5** (Good triage support, limited interactive tools) |
| **Thirona RetCAD** | **4/5** (Automated quality check indicators) | **5/5** (Interactive heatmap overlays + lesion masks) | **5/5** (Continuous quantitative risk + ICDR stages) | **3/5** (Integrated into heavy PACS/camera suites) | **4/5** (PACS-aligned dark interface) | **4/5** (Structured diagnostic summary) | **2/5** (Too complex for frontline outreach workers) | **5/5** (Superb diagnostic verification ergonomics) |
| **OHIF Viewer / Cornerstone3D** | **1/5** (No built-in image quality assessment) | **4/5** (Custom segmentation & contour overlays) | **N/A** (Diagnostic viewer only, no native AI) | **3/5** (PACS query/retrieve overhead) | **5/5** (World-class diagnostic dark theme `#0f172a`) | **2/5** (Basic screenshot/DICOM capture) | **1/5** (Requires heavy clinical network infrastructure) | **5/5** (Industry benchmark for radiologist/retinal viewing) |
| **PROPOSED: EYERIS** | **5/5** (Immediate pre-submission quality gate) | **5/5** (Dual-pane Grad-CAM + U-Net lesion masks) | **5/5** (5-class ICDR + calibrated conf + uncertainty) | **5/5** (Single-page drag-and-drop $<5$s local inference) | **5/5** (Diagnostic Slate Dark Canvas + WCAG AAA) | **5/5** (Interactive web report + `@media print` export) | **5/5** (Streamlined Intake & Quick Triage Mode) | **5/5** (Deep Explainability & Inspection Mode) |

---

## 2. In-Depth Comparative Critique

### 2.1 The "Black-Box" Dilemma vs. Clinician Trust
- **Observation**: Systems like LumineticsCore prioritize speed for medical assistants by suppressing all explainability data. While this accelerates point-of-care triage, field studies repeatedly demonstrate that consulting ophthalmologists reject automated referrals when they cannot inspect the underlying lesion features or attention maps.
- **YERIS Solution**: Implement a **Dual-Mode Experience**:
  - *Screening Mode (Default for Operators)*: Large high-contrast cards displaying Image Quality (Pass/Fail), Overall Referral Recommendation (Refer / Routine), and Action Urgency (Urgent / Routine).
  - *Clinical Inspection Mode (For Specialists)*: Unlocks side-by-side synchronized viewports, Grad-CAM opacity sliders, lesion area metrics, and probability distributions.

### 2.2 Quality Gating UX: Preventative vs. Reactive
- **Observation**: Reactive systems allow low-quality images to enter the inference pipeline, failing minutes later with an ambiguous "Analysis Error" after the patient has departed. Google ARDA and LumineticsCore succeeded in the field because their quality check is **preventative** and instantaneous.
- **YERIS Solution**: In `integration/model_orchestrator.py`, quality evaluation runs as the very first sequential stage. If the image is ungradable ($<0.6$ quality score or severe blur/underexposure), the UI immediately renders an amber/red **Quality Warning Card** with explicit instructions (e.g. *"Image underexposed. Adjust camera illumination and retake"*), halting unnecessary deep model execution.

### 2.3 The Visualization Paradox: Heatmap Occlusion vs. Diagnostic Value
- **Observation**: A common complaint about Grad-CAM heatmaps in clinical practice is that bright red/yellow heatmap overlays physically block the clinician from seeing the underlying tiny microaneurysms or subtle retinal hemorrhages they are trying to verify.
- **YERIS Solution**:
  - Provide an interactive **Opacity Slider** ($0\% \dots 100\%$) directly above the viewport.
  - Implement a **"Press-and-Hold to Compare"** interaction pattern: holding the spacebar or clicking a "Toggle Original" button instantly hides the overlay, snapping back to the raw fundus image for immediate visual confirmation.

### 2.4 Ergonomics & Reading Room Glare
- **Observation**: Commercial PACS viewers (OHIF, Zeiss FORUM) use dark gray/slate themes because retinal fundus examination requires subtle differentiation between dark red hemorrhages and dark retinal pigment epithelium. High-brightness white SaaS dashboards cause pupil constriction, washing out fine details.
- **YERIS Solution**: The primary application canvas adopts a **Diagnostic Slate Dark Theme** (`#0B0F17` base canvas, `#131B2A` elevated cards), calibrated to eliminate glare while maintaining $>10:1$ WCAG text contrast ratios.

