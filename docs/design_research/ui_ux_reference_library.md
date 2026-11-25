# EYERIS — UI/UX Reference Library & Clinical Design Patterns
**Subsystem**: UI/UX Research & Design Architecture  
**Role**: Senior Software Architect & Lead Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Formal Research Deliverable  

---

## 1. Verified Clinical References & Source Documentation

| Reference Product / System | Domain | Source URL / Authority | Key Feature / Documentation Citation |
| :--- | :--- | :--- | :--- |
| **LumineticsCore (IDx-DR)** | Autonomous DR Screening | [Digital Diagnostics Clinical Overview](https://digitaldiagnostics.com/products/eye-disease/luminetics-core/) / [FDA K172818 Summary](https://www.accessdata.fda.gov/cdrh_docs/pdf17/DEN170018.pdf) | Point-of-care $<30$s triage; operator-level binary referral output; non-mydriatic image quality gating. |
| **Eyenuk EyeArt** | Cloud DR / DME AI Triage | [Eyenuk Product Documentation](https://www.eyenuk.com/us-en/eyeart/) / [FDA K200667 Summary](https://www.accessdata.fda.gov/cdrh_docs/pdf20/K200667.pdf) | Bilateral eye (OD/OS) reporting; mtmDR vs. vtDR distinction; under 60-second processing; CPT 92229 billing support. |
| **Google Health ARDA** | Frontline Population Screening | [Google Health ARDA Research](https://research.google/teams/health/applied-ai/screening-and-diagnostics/retinal-disease/) / [Aravind Eye Hospital Study (Ophthalmology 2021)](https://www.aaojournal.org/article/S0161-6420(20)30932-9/fulltext) | Field deployment in rural India and Thailand; high-throughput image upload; real-time quality warnings to prevent recall. |
| **Thirona RetCAD** | Explainable Retinal AI | [Thirona RetCAD System Overview](https://thirona.eu/retcad/) / [NIDEK NAVIS-EX Integration](https://www.nidek-intl.com/product/ophthalmology/diagnostic/software/retcad.html) | Interactive heatmap overlay toggle; ICDR grading scales; microaneurysm and exudate lesion localization. |
| **OHIF Viewer & Cornerstone3D** | Web Medical Imaging Viewer | [OHIF Documentation & Live Demo](https://viewer.ohif.org/) / [GitHub Repository](https://github.com/OHIF/Viewers) | Diagnostic dark mode (`#0f172a`); 1x1, 1x2 comparative viewports; window/level, pan/zoom, measurement tools. |
| **IBM Carbon for Healthcare** | Enterprise Clinical Design System | [IBM Carbon Healthcare Patterns](https://www.carbondesignsystem.com/community/domain-guidance/health/) | Medical card layouts, critical alert banners, WCAG AAA compliant color tokens, clinical data tables. |
| **NHS Digital Design System** | Public Health Digital Standards | [NHS Digital Service Manual](https://service-manual.nhs.uk/) | Clear medical typography, patient identification banners, high-contrast accessible triage callouts. |
| **Radicle / Philips HealthSuite** | Medical Device UX Standards | [Philips HealthSuite Digital Platform](https://www.philips.com/a-w/about/healthsuite.html) | DICOM viewer ergonomics, progressive disclosure for complex diagnostic findings, audit logging. |

---

## 2. Evaluation of Clinical Design Patterns

### 2.1 Navigation & Information Architecture (IA)
- **Clinical Best Practice**: A persistent **Global App Header** showing patient context (Case ID, Patient Identifier hash, Date/Time, Connection/DB status), coupled with a horizontal workflow progress breadcrumb:
  `1. Intake / Upload` $\rightarrow$ `2. Quality Verification` $\rightarrow$ `3. AI Inference & Grading` $\rightarrow$ `4. Specialist Review / Report`.
- **Reference**: NHS Digital and Epic Hyperspace enforce a persistent "Patient Context Bar" at the top of every screen. Even when drilling down into deep Grad-CAM heatmaps, the clinician never loses sight of which patient is being inspected.
- **EYERIS Architecture**:
  - Top Navigation: Brand badge, active Screening Mode switcher (Quick Screening vs Specialist Review), system health indicator, user profile.
  - Sub-navigation: Tabs for *Overview*, *Fundus Viewer (Heatmap/Masks)*, *Clinical Decision*, and *Full Report*.

---

### 2.2 Color System & Contrast Calibration (WCAG 2.1 AA/AAA)
Retinal fundus images are dominantly reddish-orange and dark ochre with subtle yellow (hard exudates) and dark red (microaneurysms, blot hemorrhages). UI colors must never visually compete with the retinal tissue or cause chromatic adaptation fatigue.

```
+---------------------------------------------------------------------------------------+
| EYERIS CLINICAL COLOR PALETTE REFERENCE                                               |
+---------------------------------------------------------------------------------------+
| Role            | Token Name          | Hex Code | WCAG Contrast | Clinical Meaning   |
+---------------------------------------------------------------------------------------+
| Base Canvas     | --bg-canvas         | #0B0F17  | >14:1 on text | Deepest slate      |
| Surface Card    | --bg-surface        | #131B2A  | >11:1 on text | Elevated card      |
| Border / Muted  | --border-subtle     | #233148  | >4.5:1        | Section divider    |
| Text Primary    | --text-primary      | #F1F5F9  | 14.8:1        | Primary headers    |
| Text Muted      | --text-secondary    | #94A3B8  | 6.2:1         | Captions, units    |
+---------------------------------------------------------------------------------------+
| Grade 0 (No DR) | --severity-grade-0  | #10B981  | >4.5:1 (Dark) | Normal / Low Risk  |
| Grade 1 (Mild)  | --severity-grade-1  | #06B6D4  | >4.5:1 (Dark) | Microaneurysms only|
| Grade 2 (Mod)   | --severity-grade-2  | #F59E0B  | >4.5:1 (Dark) | Referable DR       |
| Grade 3 (Severe)| --severity-grade-3  | #F97316  | >4.5:1 (Dark) | Prompt Referral    |
| Grade 4 (PDR)   | --severity-grade-4  | #EF4444  | >4.5:1 (Dark) | Urgent Referral    |
+---------------------------------------------------------------------------------------+
| Quality Reject  | --quality-error     | #DC2626  | >4.5:1 (Dark) | Mandatory Recapture|
| Uncertainty     | --uncertainty-warn  | #8B5CF6  | >4.5:1 (Dark) | Human Review Gate  |
+---------------------------------------------------------------------------------------+
```

---

### 2.3 Typography Hierarchy in Medical UIs
- **Font Stack**: Clean, highly legible sans-serif with distinct numeric glyphs (tabular numbers for data tables): `Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
- **Numeric Font Feature**: `font-feature-settings: "tnum"` to ensure numbers in probability tables and confidence gauges align vertically without horizontal jitter.
- **Type Scale**:
  - `Display / H1`: 24px (1.5rem), Semibold (600) — Case ID / Primary Result
  - `Section / H2`: 18px (1.125rem), Medium (500) — Viewport & Card Headers
  - `Body`: 14px (0.875rem), Regular (400) — Rationale & clinical notes
  - `Label / Metric`: 12px (0.75rem), Medium (500), Uppercase tracking +0.05em — Field metadata
  - `Legal / Disclaimer`: 11px (0.6875rem), Regular (400), Muted italic — Medical disclaimer

---

### 2.4 Retinal Image Viewport & Dual-Pane Viewer Ergonomics
Drawing directly from **OHIF Viewer** and **Thirona RetCAD**:
- **Dual-Pane Side-by-Side Viewport**:
  - *Left Pane*: Original Preprocessed Fundus Photograph (True-color RGB).
  - *Right Pane*: Explainability Viewport (Grad-CAM Heatmap Overlay or U-Net Lesion Segmentation Masks).
- **Synchronized Viewport Navigation**: Panning or zooming the left viewport automatically updates the scale and offset of the right viewport, maintaining exact anatomical alignment.
- **Interactive Layer Stack**:
  - `Base`: Original Fundus Photograph.
  - `Layer 1`: Grad-CAM Class Activation Map (Jet/Turbo colormap with opacity slider from $0\%$ to $100\%$).
  - `Layer 2`: Hard Exudates Mask (Bright yellow outline/fill).
  - `Layer 3`: Hemorrhages Mask (Red outline/fill).
  - `Layer 4`: Microaneurysms Mask (Cyan point markers).
- **Viewport Controls**:
  - Reset View / Fit to Window.
  - Interactive Zoom ($50\% - 400\%$) and Smooth Pan.
  - Invert Colors (Green-channel isolation mode for vascular inspection).
  - Toggle Heatmap On/Off with a single keystroke (`H`).

---

### 2.5 Clinical Data Visualization & Confidence Gauges
- **DR Severity Scale (ICDR 0–4)**: A 5-segment horizontal segmented progress track with distinct color bands and active indicator caret. Avoid continuous ungraduated dials which imply false precision.
- **Calibrated Confidence Meter**: A semi-circular radial gauge or precision progress bar showing temperature-calibrated posterior probability ($0\% - 100\%$) with an explicit **Uncertainty Margin** shaded in translucent violet.
- **Lesion Area Quantification Table**: Tabular breakdown of segmented lesion pixel areas and estimated percentages of macular/retinal coverage.

---

### 2.6 Printable Clinical Screening Report View
- **Print Stylesheet (`@media print`)**: Automatically switches background to crisp pure white (`#ffffff`), typography to high-contrast dark slate (`#0f172a`), suppresses interactive viewport buttons and sliders, and lays out a formal two-column clinical summary:
  - Header: Clinic Name, Case ID, Barcode/QR Code, Timestamp.
  - Left Column: Side-by-side thumbnail print of Original Image and Grad-CAM Heatmap.
  - Right Column: Automated ICDR Grading, Quality Metrics, Referral Recommendation, Rationale.
  - Bottom Banner: Prominent legal research disclaimer and space for verifying clinician's signature.

