# EYERIS — UI/UX Design Decision Log & Architectural Traceability
**Subsystem**: UI/UX Governance & Decision Architecture  
**Role**: Senior Product Designer & Lead Integration Architect (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 2026  
**Status**: Proposal for Design Approval Gate  

---

## 1. Decision Log Summary

This document formalizes all architectural, visual, and interaction design decisions established during the UI/UX Research Gate. Every decision is grounded in empirical evidence from commercial medical AI systems (IDx-DR, EyeArt, RetCAD), clinical PACS viewers (OHIF), or high-productivity SaaS benchmarks (Linear, Stripe, Vercel), ensuring complete traceability from clinical requirement to implementation.

---

## 2. Formal Decision Records

### DEC-01: Diagnostic Slate Dark Theme vs. Light Mode
- **Status**: **Approved for Gate Review**
- **Reference Source**: OHIF Diagnostic Medical Viewer, Carl Zeiss FORUM, Topcon Harmony PACS.
- **Observed Pattern**: Diagnostic reading rooms utilize dark gray/slate canvases (`#0B0F17` to `#1E293B`) to eliminate ocular glare and maximize contrast sensitivity when inspecting low-contrast retinal features (such as subtle microaneurysms and deep retinal hemorrhages).
- **EYERIS Adaptation**: The primary application canvas adopts a multi-tiered Diagnostic Slate Dark Palette:
  - `--eyeris-canvas: #090D16` (Deepest canvas)
  - `--eyeris-surface-1: #131C2E` (Primary card panels)
  - `--eyeris-border-subtle: #1E2C44` (Dividers)
  - Text contrast exceeds 14:1 on primary headings (WCAG AAA).
- **Reason for Adaptation**: High-glare white dashboards induce pupil constriction, causing ophthalmologist eye strain and reducing detection sensitivity for fine retinal vascular abnormalities.
- **Implementation Priority**: **Critical (Baseline in CSS Tokens)**.

---

### DEC-02: Instantaneous Pre-Inference Quality Gating
- **Status**: **Approved for Gate Review**
- **Reference Source**: Digital Diagnostics LumineticsCore (IDx-DR) FDA K172818 Summary, Google Health ARDA Field Deployments.
- **Observed Pattern**: Autonomous screening systems execute real-time image quality evaluation immediately upon photo acquisition. If quality is inadequate (due to blur, eyelid occlusion, or underexposure), the system halts inference and alerts the operator while the patient is still seated.
- **EYERIS Adaptation**:
  - In `model_orchestrator.py`, the image quality assessment executes as Stage 1.
  - If `overall_quality_score < 0.60` or `is_gradable == False`, downstream DR classification and Grad-CAM stages are bypassed.
  - The UI immediately renders a high-contrast **Quality Warning Modal** showing specific failure reasons (e.g. *"Corneal Reflection Detected"*) and practical positioning guidance (*"Adjust chin rest and instruct patient to fixate on internal target"*).
- **Reason for Adaptation**: Prevents ungradable images from generating false-negative reassuring grades, and prevents patients from departing the outreach camp prior to acquiring an adequate scan.
- **Implementation Priority**: **Critical (Active in Backend & Frontend)**.

---

### DEC-03: Decoupled Manual Review vs. Referral Recommendation
- **Status**: **Approved for Gate Review**
- **Reference Source**: NHS Diabetic Eye Screening Programme (DESP) Clinical Pathways, Eyeris Clinical Decision Engine.
- **Observed Pattern**: Conventional research models often conflate "missing model" or "technical failure" with a clinical referral recommendation, which artificially inflates false-positive referral queues at tertiary eye hospitals.
- **EYERIS Adaptation**:
  - In `integration/decision_engine.py`, when a classification model is unavailable or unharvested, the system outputs:
    - `referral_recommended: False`
    - `review_required: True`
    - `urgency: "manual_review"`
    - `rationale: "Automated classification model unavailable; manual review required before referral determination."`
- **Reason for Adaptation**: Safeguards hospital referral registries from being inundated with unassessed cases while guaranteeing that every unassessed fundus image is queued for human specialist review.
- **Implementation Priority**: **Critical (Verified in Phase 1.1)**.

---

### DEC-04: Interactive Opacity Slider & Press-and-Hold Bypass for Grad-CAM
- **Status**: **Approved for Gate Review**
- **Reference Source**: Thirona RetCAD, Academic Critiques of Saliency Maps in Ophthalmology.
- **Observed Pattern**: Static Grad-CAM attention heatmaps permanently occlude underlying retinal anatomy, preventing ophthalmologists from verifying whether an attention hotspot aligns with a true microaneurysm or an image artifact (e.g. dust on camera lens).
- **EYERIS Adaptation**:
  - Renders an interactive **Opacity Slider** ($0\% \dots 100\%$) directly in the retinal viewport toolbar.
  - Implements a **Press-and-Hold Spacebar Interaction**: holding the spacebar temporarily sets heatmap opacity to $0\%$, snapping back to the preprocessed true-color fundus image for instant visual verification.
- **Reason for Adaptation**: Empowers clinicians to rigorously audit AI saliency maps against true clinical retinal anatomy without visual occlusion.
- **Implementation Priority**: **Critical (Phase 2 Component)**.

---

### DEC-05: Strict Absence of Fabricated or Simulated Diagnostics
- **Status**: **Approved for Gate Review**
- **Reference Source**: FDA Good Machine Learning Practice (GMLP) for Medical Device Development.
- **Observed Pattern**: Research prototypes sometimes inject randomized mock predictions or synthetic accuracy charts to make early UI demos look complete, risking severe clinical misinterpretation.
- **EYERIS Adaptation**:
  - `allow_mock=False` is enforced by default in `model_orchestrator.py`.
  - When real ML weights are not loaded (e.g. prior to harvesting Member 1 or Member 2 code), the UI explicitly renders `"Model Offline — Clinical Review Required"`.
  - All mock data paths are visibly stamped with `is_synthetic: True`.
- **Reason for Adaptation**: Preserves absolute clinical and ethical credibility during SIH evaluation and expert clinical reviews.
- **Implementation Priority**: **Critical (Enforced in Code)**.

---

### DEC-06: Dual-Persona User Experience (Operator vs. Specialist Mode)
- **Status**: **Approved for Gate Review**
- **Reference Source**: Google Health ARDA (frontline technicians) vs. Topcon Harmony (ophthalmologists).
- **Observed Pattern**: Frontline screening camp operators are overwhelmed by complex multi-layer PACS tools, whereas ophthalmologists reject simplified binary interfaces that conceal diagnostic evidence.
- **EYERIS Adaptation**:
  - A persistent **Mode Switcher** in the global header toggles between:
    - **Operator Mode**: Large high-contrast cards, simplified binary referral badges, and streamlined 2-click upload workflows.
    - **Specialist Mode**: Full dual-pane synchronized viewports, Grad-CAM layer toggles, lesion area quantification tables, and epistemic uncertainty telemetry.
- **Reason for Adaptation**: Delivers an optimal user experience across both rural community outreach and tertiary hospital tele-ophthalmology environments.
- **Implementation Priority**: **High (Phase 2 UI Architecture)**.

---

### DEC-07: Web-Native Clinical Report with Pure CSS `@media print` Engine
- **Status**: **Approved for Gate Review**
- **Reference Source**: EyeArt Clinical Summary PDF, NHS DESP Examination Slips.
- **Observed Pattern**: Commercial systems rely on heavy server-side PDF generators (wkhtmltopdf, headless Chrome) that frequently introduce latency or layout formatting breaks.
- **EYERIS Adaptation**:
  - The Report screen ([Reports.jsx](file:///C:/Users/ASUS/Desktop/Eyeris/frontend/src/pages/Reports.jsx)) renders as a clean web component on screen.
  - When the browser print dialog is triggered (`Ctrl/Cmd + P`), dedicated `@media print` CSS converts the dark theme into an inverted white-paper clinical summary sheet:
    - Sets page geometry to standard A4 with clean 0.5-inch margins.
    - Inverts text to high-contrast black on white.
    - Prints fundus and Grad-CAM thumbnails side-by-side.
    - Provides a formal clinician signature and license registration sign-off block.
- **Reason for Adaptation**: Zero external dependencies, instant print generation, and flawless high-resolution export in resource-constrained rural clinics.
- **Implementation Priority**: **Critical (Already Foundationally Implemented in CSS)**.

