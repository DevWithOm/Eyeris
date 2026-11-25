# EYERIS — Unified Clinical Design Direction & Design System Specification
**Subsystem**: UI/UX Research & Design Architecture  
**Role**: Senior Software Architect & Lead Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Formal Proposal for Approval Gate  

---

## 1. Design Philosophy & Core Principles

The EYERIS user experience is built upon five foundational clinical design tenets:

1. **Clinical Trust Through Explainability, Not Black-Box Dictation**:
   The interface never displays an arbitrary grade without immediate visual evidence. Every automated recommendation is backed by synchronized Grad-CAM class activation heatmaps, temperature-calibrated confidence scores, and quantified lesion segmentation metrics.
2. **Instantaneous Preventative Quality Gating**:
   Technical quality is assessed before full inference occurs. The operator receives immediate actionable guidance on blur, illumination, or field-of-view defects while the patient is still seated in front of the fundus camera.
3. **Dual-Persona Ergonomics (Operator vs. Specialist Modes)**:
   - *Operator Mode*: Simplified, high-contrast, binary triage indicators designed for rapid throughput in rural health camps.
   - *Specialist Mode*: Comprehensive diagnostic inspection canvas equipped with dual-pane synchronized zooming, layer opacity sliders, and lesion area tables.
4. **Diagnostic Dark Canvas (Zero Eye Strain & Glare Reduction)**:
   Calibrated using deep slate and obsidian surfaces (`#0B0F17`) drawn from diagnostic radiology/ophthalmology reading room standards (OHIF, Zeiss FORUM). Eliminates screen glare and maximizes visual sensitivity to fine retinal microaneurysms.
5. **Mandatory Ethical & Regulatory Transparency**:
   A persistent, non-intrusive banner reminds operators that EYERIS is a research screening-support prototype developed for SIH PS26038, not an autonomous diagnostic medical device.

---

## 2. Visual Identity & Design Tokens

### 2.1 Color Tokens & Semantic Assignments

```css
:root {
  /* Surface & Canvas Tokens (Diagnostic Slate Theme) */
  --eyeris-canvas: #0b0f17;          /* Primary dark workspace canvas */
  --eyeris-surface-1: #111827;       /* Primary elevated cards and panels */
  --eyeris-surface-2: #1e293b;       /* Secondary inputs, toolbars, hovers */
  --eyeris-surface-3: #334155;       /* Tooltips, active highlights */
  --eyeris-border-subtle: #1e293b;   /* Low-contrast card borders */
  --eyeris-border-focus: #3b82f6;    /* Active focus rings */

  /* Text & Content Tokens */
  --eyeris-text-primary: #f8fafc;    /* High-contrast headings and values (14.8:1) */
  --eyeris-text-secondary: #94a3b8;  /* Labels, metric captions (6.2:1) */
  --eyeris-text-muted: #64748b;      /* Disabled states, subtle borders */

  /* Clinical Severity Tokens (ICDR 5-Grade Scale) */
  --eyeris-dr-grade-0: #10b981;      /* Grade 0 - No DR: Emerald Green */
  --eyeris-dr-grade-1: #06b6d4;      /* Grade 1 - Mild: Cyan / Blue-Green */
  --eyeris-dr-grade-2: #f59e0b;      /* Grade 2 - Moderate: Warm Amber */
  --eyeris-dr-grade-3: #f97316;      /* Grade 3 - Severe: Vibrant Orange */
  --eyeris-dr-grade-4: #ef4444;      /* Grade 4 - Proliferative: Crimson Red */

  /* Triage & Status Tokens */
  --eyeris-status-referral: #ef4444; /* Referral Required badge */
  --eyeris-status-routine: #10b981;  /* Routine Monitoring badge */
  --eyeris-status-quality-err: #dc2626; /* Ungradable alert */
  --eyeris-status-uncertain: #8b5cf6;/* High Uncertainty / Escalate badge */

  /* Lesion Segmentation Overlay Colors */
  --eyeris-lesion-exudate: #facc15;  /* Hard Exudates: Yellow (#FACC15) */
  --eyeris-lesion-hemorrhage: #ef4444;/* Hemorrhages: Crimson Red (#EF4444) */
  --eyeris-lesion-ma: #06b6d4;       /* Microaneurysms: Cyan Marker (#06B6D4) */
}
```

---

### 2.2 Typography System
- **Primary Typeface**: `Inter, system-ui, -apple-system, sans-serif`
- **Tabular Numerals**: `font-variant-numeric: tabular-nums` for all probability tables, quality scores, and coordinates to prevent horizontal alignment shifts during live updates.
- **Scale**:
  - `Display / Primary Result`: 28px (1.75rem), Weight 700, Line-height 1.2
  - `Card Title / Section`: 18px (1.125rem), Weight 600, Line-height 1.3
  - `Body / Clinical Rationale`: 14px (0.875rem), Weight 400, Line-height 1.5
  - `Metric Label / Badge`: 12px (0.75rem), Weight 600, Uppercase tracking +0.05em
  - `Footnote / Disclaimer`: 11px (0.6875rem), Weight 400, Italic, Color `#64748B`

---

### 2.3 Spatial System & Grid
- **8px Grid System**: All margins, paddings, and component dimensions adhere to multiples of 8px (4px for micro-spacers, 8px, 16px, 24px, 32px, 48px).
- **Responsive Layout**:
  - `Desktop (>= 1280px)`: Two-column master layout. Left: Sticky Dual-Pane Fundus Viewport ($60\%$ width). Right: Diagnostic cards and clinical recommendations ($40\%$ width).
  - `Laptop / Tablet (768px - 1279px)`: Vertically stacked layout with tabs switching between Viewport, Metrics, and Report.
  - `Mobile / Outreach Tablet (< 768px)`: Streamlined single-column view optimized for touch-based drag-and-drop screening in field camps.

---

## 3. Core Component Specifications

```
+---------------------------------------------------------------------------------------------------------+
|                                     EYERIS GLOBAL PATIENT HEADER                                        |
|  [Logo] EYERIS Screening | Case: EYE-20261116-A1B2 | Patient: #HASH-8924 | Mode: [Operator / Specialist] |
+---------------------------------------------------------------------------------------------------------+
|                                  PERSISTENT MEDICAL DISCLAIMER BANNER                                    |
|  Notice: Research screening-support prototype (SIH PS26038). Not a certified diagnostic medical device.  |
+--------------------------------------------------------------------+------------------------------------+
|                   RETINAL FUNDUS VIEWPORT (60%)                    |      DIAGNOSTIC TRIAGE (40%)       |
|                                                                    |                                    |
|  [View: Dual Synchronized]  [Heatmap Opacity: =====O== 70%]  [Reset]|  +------------------------------+  |
|  +-------------------------------+-------------------------------+  |  | QUALITY GATE: [GRADABLE]     |  |
|  |                               |                               |  |  | Score: 0.94 / 1.00            |  |
|  |                               |                               |  |  +------------------------------+  |
|  |     ORIGINAL FUNDUS PHOTO     |      GRAD-CAM HEATMAP         |  |  | DR GRADE: 2 (MODERATE NPDR)  |  |
|  |       (True Color RGB)        |     (Overlay Opacity 70%)     |  |  | [======][======][  ][  ][  ]  |  |
|  |                               |                               |  |  | Conf: 82.4% | Uncert: 11.8%   |  |
|  |                               |                               |  |  +------------------------------+  |
|  |                               |                               |  |  | REFERRAL: RECOMMENDED        |  |
|  |                               |                               |  |  | Urgency: Routine (4-8 weeks)   |  |
|  +-------------------------------+-------------------------------+  |  +------------------------------+  |
|  [v] Show Hard Exudates (1240px) [v] Show Hemorrhages (780px)      |  | CLINICAL RATIONALE:          |  |
|  [Hold SPACE to inspect original fundus]                           |  | Moderate NPDR with macular   |  |
|                                                                    |  | exudates. Dilated exam req.  |  |
|                                                                    |  +------------------------------+  |
|                                                                    |  [ View Full Clinical Report ]     |  |
+--------------------------------------------------------------------+------------------------------------+
```

### 3.1 Component 1: Retinal Image Upload Dropzone (`ImageDropzone.jsx`)
- Supports drag-and-drop or file browsing for JPEG, PNG, and TIFF formats.
- Pre-upload client validation: verifies file size ($<15$ MB) and image aspect ratio.
- Visual state transitions: Idle (dashed border with retinal camera icon), Drag-Over (vibrant blue border with subtle glow), Uploading (animated progress bar with elapsed milliseconds counter), and Completed.

### 3.2 Component 2: Immediate Quality Assessment Badge & Alert (`QualityBadge.jsx`)
- Color-coded indicator: Emerald Green (`GRADABLE`), Warm Amber (`REVIEW_REQUIRED`), Crimson Red (`UNGRADABLE / RECAPTURE`).
- Metric tooltip revealing sharpness, illumination, contrast, and field-of-view scores.
- When ungradable, renders an immediate modal explaining why the image failed (e.g. *"Corneal glare obstruction"* or *"Blur detected"*) and offering clear instructions to the operator.

### 3.3 Component 3: 5-Grade Severity Indicator Card (`DRGradeCard.jsx`)
- Prominent badge displaying the ICDR DR Grade (`0` to `4`) and clinical name (`No DR`, `Mild`, `Moderate`, `Severe`, `Proliferative DR`).
- 5-segment horizontal bar visually conveying disease progression.
- Raw softmax class distribution accordion for specialist review.

### 3.4 Component 4: Calibrated Confidence & Uncertainty Gauge (`ConfidenceGauge.jsx`)
- Visual display of temperature-calibrated posterior probability ($0\% - 100\%$).
- Distinct violet uncertainty indicator highlighting when the case borders on the decision threshold ($>0.35$).
- Explicit "Low Uncertainty / High Reliability" vs. "High Uncertainty / Specialist Confirmation Required" status badge.

### 3.5 Component 5: Dual-Pane Synchronized Viewport (`DualImageViewer.jsx`)
- Side-by-side comparison of original fundus image and Grad-CAM class activation heatmap.
- Opacity slider ($0\% - 100\%$) directly overlaid on the header toolbar.
- Synchronized pan and zoom powered by mouse wheel and drag gestures.
- Spacebar shortcut: Press and hold spacebar to momentarily hide all overlays and reveal the raw fundus image.

### 3.6 Component 6: Printable Structured Screening Report (`ScreeningReportView.jsx`)
- Formatted two-column clinical report view with export to PDF / Print.
- Automatic application of `@media print` stylesheet switching to high-contrast white paper styling with medical barcodes, patient ID hashes, timestamp, and signature blocks.
