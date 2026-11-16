# EYERIS — UI/UX Design Decision Log & Architectural Traceability (Final Gate Closure)
**Subsystem**: UI/UX Governance & Decision Architecture  
**Role**: Senior Healthcare UX Architect & Design Systems Lead (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 16, 2026  
**Status**: Final Design Approval Gate Specification (Referral Terminology Standardized)  

---

## 1. Member 4 Approved Design Decisions (Final Gate Closure)

The following twelve design governance decisions have been formally approved and logged as binding architectural requirements:

```
+---------------------------------------------------------------------------------------------------------+
|                                  MEMBER 4 APPROVED DESIGN DECISION INDEX                                |
+---------+---------------------------------------------------------------------+-------------------------+
| DEC ID  | Decision Title                                                      | Architectural Scope     |
+---------+---------------------------------------------------------------------+-------------------------+
| DEC-01  | Diagnostic Slate Dark Palette (#090D16 Canvas / #131C2E Cards)       | Visual & Ergonomics     |
| DEC-02  | Instantaneous In-Chair Pre-Inference Quality Gating                 | Clinical Safety & Intake|
| DEC-03  | Decoupled States with Strict 4-Tier Precedence & Referral Model     | Backend & State Machine |
| DEC-04  | Interactive Opacity Slider & Hold Spacebar Raw Fundus Bypass        | Retinal Viewport Tool   |
| DEC-05  | Mandatory Attention Map Causality Guardrail Notice                  | Explainability Policy   |
| DEC-06  | Strict Absence of Fabricated Metrics & Labeled Illustrative Data    | Data Integrity & Ethics |
| DEC-07  | Configurable Provisional Engineering Values (0.60 Quality, 0.35 Unc)| Telemetry Architecture  |
| DEC-08  | Role-Aware Presentation Views on Unified Decision Pipeline Engine    | Multi-User UX           |
| DEC-09  | Multi-Channel Encoding (Zero Color-Alone Status Representation)     | WCAG 1.4.1 Accessibility|
| DEC-10  | Mathematically Verified Contrast (Corrected Ratios & #2563EB Button)| WCAG 1.4.3 & 1.4.11     |
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
- **EYERIS Adaptation**: In `model_orchestrator.py`, quality evaluation runs as the primary stage. If `overall_quality_score < 0.60` (provisional engineering threshold) or `is_gradable == False`, deep classification is halted. The UI renders an immediate **Quality Warning Modal** specifying defects and actionable reacquisition instructions. Referral status is set strictly to **`NOT_ASSESSED`**.
- **Reason for Adaptation**: Prevents ungradable images from generating false-negative reassuring grades, and prevents patients from departing before obtaining an adequate scan.
- **Priority**: Critical.

---

### DEC-03: Decoupled Architectural States with Strict 4-Tier Precedence & Referral Model
- **Reference Source**: NHS Diabetic Eye Screening Programme (DESP) Clinical Pathways, Eyeris Clinical Decision Engine.
- **Observed Pattern**: Research prototypes frequently conflate "offline model" or "image quality failure" with a clinical referral, artificially flooding tertiary hospital referral queues, or misleadingly report `Referral: FALSE` for unassessed scans.
- **EYERIS Adaptation**: Formally establishes a 4-tier precedence hierarchy with a standardized 4-value referral model:
  1. *State B (Precedence 1 - Highest): Image Quality Failure*: `is_gradable: False`, `urgency: "recapture_required"`. Halts grading; if recapture unavailable, routes to manual review; referral status is strictly **`NOT_ASSESSED`** (never reported as negative or false); overrides all downstream models.
  2. *State A (Precedence 2): Model Unavailable*: Classification withheld; clinical review required; referral status is strictly **`NOT_ASSESSED`**; no negative result inferred.
  3. *State C (Precedence 3): High Model Uncertainty*: Uncertainty exceeds threshold (`0.35`); classification withheld or flagged uncertain; clinical review required; referral status is strictly **`NOT_DETERMINED`**; high uncertainty alone never sets referral to `INDICATED`.
  4. *State D (Precedence 4 - Lowest): Referral Decision*: Referral status is strictly **`INDICATED`** or **`NOT_INDICATED`**, and urgency tier is supplied directly by backend policy. Frontend does not hardcode universal urgency mappings or invent clinical timeframes.
- **Reason for Adaptation**: Protects hospital referral registries from false-positive saturation while guaranteeing every unassessed or uncertain case is routed to human clinician review without misleading negative labels.
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

### DEC-06: Strict Absence of Fabricated Metrics & Labeled Illustrative Data
- **Reference Source**: FDA Good Machine Learning Practice (GMLP) for Medical Device Development.
- **Observed Pattern**: Early prototypes sometimes inject unannotated mock predictions or synthetic metrics to make demos appear complete, risking clinical confusion.
- **EYERIS Adaptation**:
  - `allow_mock=False` is enforced by default in `model_orchestrator.py`.
  - If real weights are unharvested, the UI displays `"Model Offline — Clinical Review Required"`.
  - All wireframe numbers and clinical statements are explicitly labeled as `[Illustrative Example: e.g. N]`.
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
  2. An explicit text label (e.g. `"Grade 4: PDR"`).
  3. A numeric severity level.
- **Reason for Adaptation**: Complete accessibility for color-blind practitioners and unambiguous visual parsing.
- **Priority**: Critical.

---

### DEC-10: Mathematically Verified Contrast (Corrected Ratios & #2563EB Standard)
- **Reference Source**: WCAG 2.2 Relative Luminance Standards (1.4.3 & 1.4.11).
- **Observed Pattern**: Claiming compliance without verifying exact relative luminance, leading to reporting errors and white-on-blue text contrast failures.
- **EYERIS Adaptation**:
  - Verified exact mathematical contrast ratios for all colors.
  - Corrected reported discrepancies: `#3B82F6` focus indicator achieves **4.63:1** against surface (passes WCAG 1.4.11 $\ge 3.0:1$); `#67E8F9` achieves **11.75:1**; `#FEF08A` achieves **14.63:1**.
  - Identified that `#3B82F6` with white text yields **3.68:1** (failing normal text AA 4.5:1). Standardized primary button backgrounds on `#2563EB` (luminance 0.1537), achieving **5.17:1** with white text (`#FFFFFF`) and **3.29:1** against dark surface (passing both WCAG 1.4.3 and 1.4.11).
- **Reason for Adaptation**: Absolute mathematical accessibility compliance without false claims.
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
