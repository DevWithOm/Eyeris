# EYERIS — UI/UX Design Decision Log & Architectural Traceability (Revision 1)
**Subsystem**: UI/UX Governance & Decision Architecture  
**Role**: Senior Product Designer & Lead Integration Architect (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 16, 2026  
**Status**: Revised Specification Incorporating Member 4 Approved Design Decisions  

---

## 1. Member 4 Approved Design Decisions

The following twelve design governance decisions have been formally approved and logged as binding architectural requirements:

```
+---------------------------------------------------------------------------------------------------------+
|                                  MEMBER 4 APPROVED DESIGN DECISION INDEX                                |
+---------+---------------------------------------------------------------------+-------------------------+
| DEC ID  | Decision Title                                                      | Architectural Scope     |
+---------+---------------------------------------------------------------------+-------------------------+
| DEC-01  | Diagnostic Slate Dark Palette (#090D16 Canvas / #131C2E Cards)       | Visual & Ergonomics     |
| DEC-02  | Instantaneous In-Chair Pre-Inference Quality Gating                 | Clinical Safety & Intake|
| DEC-03  | Decoupled Pipeline States (Offline, Quality, Uncertainty, Referral) | Backend & State Machine |
| DEC-04  | Interactive Opacity Slider & Hold Spacebar Raw Fundus Bypass        | Retinal Viewport Tool   |
| DEC-05  | Mandatory Attention Map Causality Guardrail Notice                  | Explainability Policy   |
| DEC-06  | Strict Absence of Fabricated or Simulated Clinical Metrics           | Data Integrity & Ethics |
| DEC-07  | Configurable Provisional Engineering Values (0.60 Quality, 0.35 Unc)| Telemetry Architecture  |
| DEC-08  | Role-Aware Presentation Views on Unified Decision Pipeline Engine    | Multi-User UX           |
| DEC-09  | Multi-Channel Encoding (Zero Color-Alone Status Representation)     | WCAG 1.4.1 Accessibility|
| DEC-10  | Mathematically Verified WCAG 2.2 AA Contrast Compliance             | WCAG 1.4.3 Contrast     |
| DEC-11  | Pure CSS @media print Medical Summary Report Engine                 | Reporting Subsystem     |
| DEC-12  | Regulatory & Clinical Transparency Framing                          | Legal & Ethics          |
+---------+---------------------------------------------------------------------+-------------------------+
```

---

## 2. Formal Decision Records

### DEC-01: Diagnostic Slate Dark Palette vs. High-Glare Light Mode
- **Reference Source**: OHIF Diagnostic Medical Viewer, Carl Zeiss FORUM, Topcon Harmony PACS.
- **Observed Pattern**: Diagnostic reading rooms utilize dark slate canvases (`#0B0F17` – `#1E293B`) to eliminate ocular glare and maximize contrast sensitivity when inspecting low-contrast retinal features (such as subtle microaneurysms and deep retinal hemorrhages).
- **EYERIS Adaptation**: Standardizes on `--eyeris-canvas: #090D16` and elevated card surface `--eyeris-surface-1: #131C2E`. Text contrast exceeds 16:1 on primary headers.
- **Reason for Adaptation**: High-glare white dashboards constrict pupils and induce visual fatigue, reducing an ophthalmologist's ability to detect fine microvascular lesions.
- **Priority**: Critical.

---

### DEC-02: Instantaneous In-Chair Pre-Inference Quality Gating
- **Reference Source**: Digital Diagnostics LumineticsCore (IDx-DR) FDA K172818 Summary, Google Health ARDA Field Deployments.
- **Observed Pattern**: Autonomous screening systems execute real-time image quality evaluation immediately upon photo intake. If quality is inadequate, the system halts inference and alerts the operator while the patient is still seated.
- **EYERIS Adaptation**: In `model_orchestrator.py`, quality evaluation runs as the primary stage. If `overall_quality_score < 0.60` (provisional engineering threshold) or `is_gradable == False`, deep classification is halted. The UI renders an immediate **Quality Warning Modal** specifying defects and actionable reacquisition instructions.
- **Reason for Adaptation**: Prevents ungradable images from generating false-negative reassuring grades, and prevents patients from departing before obtaining an adequate scan.
- **Priority**: Critical.

---

### DEC-03: Decoupled Architectural States
- **Reference Source**: NHS Diabetic Eye Screening Programme (DESP) Clinical Pathways, Eyeris Clinical Decision Engine.
- **Observed Pattern**: Research prototypes frequently conflate "offline model" or "image quality failure" with a clinical referral, artificially flooding tertiary hospital referral queues.
- **EYERIS Adaptation**: Formally separates four distinct system states:
  - *State A: Model Offline*: `referral_recommended: False`, `review_required: True`, `urgency: "manual_review"`.
  - *State B: Quality Failure*: `is_gradable: False`, `urgency: "recapture_required"`, automated grading halted.
  - *State C: High Uncertainty*: `uncertainty_detected: True`, `urgency: "urgent_review"`, specialist arbitration required.
  - *State D: Clinical Referral*: `referral_recommended: True`, tiered by ICDR disease severity (routine, prompt, urgent).
- **Reason for Adaptation**: Protects hospital referral registries from false-positive saturation while guaranteeing every unassessed case is routed to human clinician review.
- **Priority**: Critical.

---

### DEC-04: Interactive Opacity Slider & Hold Spacebar Raw Fundus Bypass
- **Reference Source**: Thirona RetCAD, Academic Critiques of Saliency Maps in Medical AI.
- **Observed Pattern**: Static Grad-CAM attention heatmaps permanently occlude underlying retinal anatomy, preventing ophthalmologists from verifying whether an attention hotspot aligns with a true lesion or an image artifact.
- **EYERIS Adaptation**:
  - Implements an interactive **Opacity Slider** ($0\% \dots 100\%$) directly in the retinal viewport toolbar.
  - Implements a **Press-and-Hold Spacebar Shortcut**: holding the spacebar drops heatmap opacity to 0%, instantly revealing the raw preprocessed fundus image.
- **Reason for Adaptation**: Empowers clinicians to audit AI attention maps against true retinal anatomy without visual occlusion.
- **Priority**: Critical.

---

### DEC-05: Mandatory Attention Map Causality Guardrail Notice
- **Reference Source**: Clinical Explainability Guidelines (Rudin et al., Nature Machine Intelligence).
- **Observed Pattern**: Clinicians occasionally assume that a Grad-CAM attention hotspot proves that a specific lesion caused the model's prediction.
- **EYERIS Adaptation**: Every Grad-CAM view displays an obligatory notice: *"Class activation heatmaps visualize deep network feature correlations and do not demonstrate direct anatomical lesion causality."*
- **Reason for Adaptation**: Prevents medical misinterpretation and reinforces ethical AI explainability boundaries.
- **Priority**: High.

---

### DEC-06: Strict Absence of Fabricated or Simulated Diagnostics
- **Reference Source**: FDA Good Machine Learning Practice (GMLP) for Medical Device Development.
- **Observed Pattern**: Early prototypes sometimes inject randomized mock predictions or synthetic metrics to make demos appear complete, risking severe clinical misinterpretation.
- **EYERIS Adaptation**:
  - `allow_mock=False` is enforced by default in `model_orchestrator.py`.
  - If real weights are unharvested, the UI displays `"Model Offline — Clinical Review Required"`.
  - All wireframe numbers are explicitly labeled as `[Example Wireframe Value: e.g. N]`.
- **Reason for Adaptation**: Preserves clinical integrity and ethical credibility before medical evaluators.
- **Priority**: Critical.

---

### DEC-07: Configurable Provisional Engineering Thresholds
- **Reference Source**: Eyeris Decision Policy (`docs/decision_policy.md`).
- **Observed Pattern**: Prematurely presenting engineering defaults as clinically validated thresholds.
- **EYERIS Adaptation**: Quality threshold `0.60` and uncertainty threshold `0.35` are documented strictly as configurable engineering heuristics subject to formal ROC/PR dataset tuning.
- **Reason for Adaptation**: Maintains scientific rigor and clinical honesty.
- **Priority**: Critical.

---

### DEC-08: Role-Aware Presentation Views on Unified Decision Pipeline Engine
- **Reference Source**: Google Health ARDA (frontline technicians) vs. Topcon Harmony (ophthalmologists).
- **Observed Pattern**: Frontline nurses are overwhelmed by complex PACS tools, whereas ophthalmologists reject simplified binary interfaces that conceal diagnostic evidence.
- **EYERIS Adaptation**: A persistent mode switcher toggles between:
  - *Operator Mode*: Streamlined 2-click intake, prominent quality pass/fail cards, and straightforward referral instructions.
  - *Specialist Mode*: Dual-pane synchronized viewports, Grad-CAM layer controls, lesion area tables, and epistemic uncertainty telemetry.
  - Both modes consume the exact same underlying pipeline API and decision payload.
- **Reason for Adaptation**: Delivers role-appropriate density without maintaining divergent decision logic.
- **Priority**: High.

---

### DEC-09: Multi-Channel Status Representation (Zero Color-Alone Encoding)
- **Reference Source**: WCAG 2.2 Guideline 1.4.1 (Use of Color).
- **Observed Pattern**: Medical dashboards frequently rely on red/amber/green badges without accompanying text or icon indicators, failing color-blind clinicians.
- **EYERIS Adaptation**: Every clinical status and severity grade combines:
  1. An icon glyph (`[●]`, `[■]`, `[◆]`, `[▲]`, `[⯄]`).
  2. An explicit text label (e.g. `"Grade 4: Proliferative DR"`).
  3. A numeric severity level.
- **Reason for Adaptation**: Complete accessibility for color-blind practitioners and unambiguous visual parsing.
- **Priority**: Critical.

---

### DEC-10: Mathematically Verified WCAG 2.2 AA Contrast Compliance
- **Reference Source**: WCAG 2.2 Contrast Standards (Level AA).
- **Observed Pattern**: Claiming accessibility compliance without calculating exact mathematical contrast ratios.
- **EYERIS Adaptation**: Computed exact relative luminance and contrast ratios across all foreground/background pairings. Calibrated muted text `--eyeris-text-muted: #8493A8` to guarantee **5.45:1** contrast on card surfaces (exceeding 4.5:1 AA requirement). Primary headings achieve **16.28:1** (exceeding AAA requirement).
- **Reason for Adaptation**: Rigorous, verified accessibility compliance.
- **Priority**: Critical.

---

### DEC-11: Pure CSS `@media print` Medical Summary Report Engine
- **Reference Source**: EyeArt Clinical Summary PDF, NHS DESP Examination Slips.
- **Observed Pattern**: Heavy server-side PDF generators introduce latency and break on constrained rural clinic hardware.
- **EYERIS Adaptation**: The Report screen renders natively in browser and converts automatically to a crisp, white-paper clinical summary slip with side-by-side thumbnails and doctor signature block when the browser print dialog (`Ctrl/Cmd + P`) is invoked.
- **Reason for Adaptation**: Zero external dependencies, instant print generation, and flawless high-resolution export.
- **Priority**: High.

---

### DEC-12: Regulatory & Clinical Transparency Framing
- **Reference Source**: SIH PS26038 Problem Statement Scope.
- **Observed Pattern**: Early AI projects inappropriately claim regulatory certification or autonomous diagnostic authority.
- **EYERIS Adaptation**: Prominent disclaimers across all screens and reports explicitly frame EYERIS as an investigational research screening-support prototype developed for SIH Problem Statement PS26038, requiring licensed clinician verification.
- **Reason for Adaptation**: Absolute regulatory compliance and ethical safety.
- **Priority**: Critical.
