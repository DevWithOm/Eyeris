# EYERIS — UI/UX Design Revision 2 Final Safety & Accessibility Audit
**Role**: Senior Healthcare UX Architect & Design Systems Lead (Member 4)  
**Date**: November 16, 2026  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System (SIH Problem Statement PS26038)  
**Branch**: `om`  
**Current HEAD**: `b1df6c9`  
**Upstream Tracking**: `origin/om` (synchronized)  
**Status**: **AWAITING MEMBER 4 DESIGN IMPLEMENTATION APPROVAL** (No UI implementation code written; zero Git commits or pushes performed)

---

## 1. Repository Safety & HEAD Commit Verification

### 1.1 Git History & HEAD Verification
- **Current Branch**: `om`
- **Current HEAD Commit**: `b1df6c9` (`docs(design): complete Revision 1 incorporating 12 Member 4 approved design decisions`)
- **Upstream Tracking**: `origin/om` (up-to-date)
- **Explanation of HEAD Progression (`bf5b093` $\rightarrow$ `76900d3` $\rightarrow$ `b1df6c9`)**:
  1. Commit `bf5b093` marked the completion of the Phase 1.1.2 Final Commit Gate and evidence audit.
  2. When the user issued the Design Approval Gate request, the initial 5 design research documents were generated. Upon receiving the user's explicit directive to *"push to om too after every phase"* and subsequent *"Continue"* instruction, commit `76900d3` (`docs(design): complete UI/UX research review...`) was created and pushed.
  3. When the user issued Revision 1 instructions, the updates were generated, and upon the subsequent *"Continue"* command, commit `b1df6c9` (`docs(design): complete Revision 1...`) was created and pushed to `origin/om`.
  4. In this current Revision 2 turn, **strict adherence to Git safety is maintained**: zero commits or pushes have been performed. All Revision 2 updates exist exclusively as local working-tree modifications awaiting your explicit review.

### 1.2 Working Tree Status
- **Modified Tracked Files**:
  - `docs/design_research/component_specification.md`
  - `docs/design_research/design_approval_report.md`
  - `docs/design_research/design_decision_log.md`
  - `docs/design_research/final_design_system.md`
  - `docs/design_research/screen_by_screen_blueprint.md`
- **Untracked File Created**:
  - `docs/design_research/design_revision_2_audit.md` (this audit deliverable)
- **Zero Modifications Outside `docs/design_research/`**: No React components altered, no backend routes changed, no packages installed.

---

## 2. Summary of Changes Made in Revision 2

1. **State C Referral Rule Correction**: Fixed the critical flaw where Revision 1 previously indicated `State C: Referral = TRUE`. In Revision 2, **high uncertainty alone never sets `Referral = TRUE`**; referral status is explicitly set to **`Not determined`** pending clinical arbitration.
2. **State D Referral/Urgency Policy Decoupling**: Removed all hardcoded frontend urgency mappings (e.g. universal Grade 2–4 mappings) and invented clinical timeframes (e.g. "1–2 weeks"). The frontend strictly renders the referral recommendation and urgency tier supplied directly by the backend decision policy payload.
3. **Clinical State Precedence Formalized**: Documented an unambiguous 4-tier precedence hierarchy (Quality Failure > Model Unavailable > Model Uncertainty > Referral Indicated).
4. **Complete Illustrative Content Annotation**: Removed all unannotated numbers across wireframes and mockups. Every figure is explicitly labeled as `[Illustrative Example: e.g. N]`, preventing confusion with real patient findings.
5. **Exact Contrast Calculation & Button Standardization**: Corrected all mathematical contrast values using the official WCAG relative-luminance formula. Standardized primary buttons on `#2563EB` (luminance 0.1537) to guarantee **5.17:1** contrast with white text (`#FFFFFF`), replacing `#3B82F6` (which failed at 3.68:1).
6. **Consistent Document Synchronization**: Updated all five design documents simultaneously with zero cross-document contradictions.

---

## 3. Clinical State Model & Precedence Hierarchy

```
+---------------------------------------------------------------------------------------------------------+
|                                    CLINICAL STATE ARCHITECTURE & PRECEDENCE                             |
+-------------+-----------------------+--------------------------+----------------------------------------+
| Precedence  | State Name            | Qualifying Conditions    | Clinical Decision & Behavior           |
+-------------+-----------------------+--------------------------+----------------------------------------+
| PRIORITY 1  | State B: Image Quality| quality < 0.60 OR        | • Grading HALTED                       |
| (Highest)   | Failure               | is_gradable == False     | • Recapture required                   |
|             |                       |                          | • If recapture fails: Manual Review    |
|             |                       |                          | • Referral: FALSE / INVALID            |
|             |                       |                          | • Never overridden by model confidence |
+-------------+-----------------------+--------------------------+----------------------------------------+
| PRIORITY 2  | State A: Model        | Quality passes, but      | • Classification WITHHELD              |
|             | Unavailable           | weights missing/offline  | • Clinical review REQUIRED             |
|             |                       |                          | • No negative result inferred          |
|             |                       |                          | • Referral: FALSE / NOT DETERMINED     |
+-------------+-----------------------+--------------------------+----------------------------------------+
| PRIORITY 3  | State C: High Model   | Quality passes, model    | • Classification flagged as UNCERTAIN  |
|             | Uncertainty           | runs, but unc > 0.35 OR  | • Clinical review REQUIRED             |
|             |                       | is_uncertain == True     | • Referral status: NOT DETERMINED      |
|             |                       |                          | • Never automatically sets Referral=TRUE|
+-------------+-----------------------+--------------------------+----------------------------------------+
| PRIORITY 4  | State D: Referral     | Quality passes, model    | • Staging: Stated by backend grade     |
| (Lowest)    | Decision (Policy)     | available, unc <= 0.35   | • Referral: Determined by backend      |
|             |                       |                          | • Urgency: Determined by backend       |
|             |                       |                          | • Human review: Stated by backend      |
+-------------+-----------------------+--------------------------+----------------------------------------+
```

---

## 4. Referral and Urgency Policy Dependencies

The frontend has been decoupled from any hardcoded diagnostic assumptions:
- **Screening Grade**: Displayed strictly from `screening_data.classification.predicted_grade` and `grade_name`.
- **Referral Indication**: Displayed strictly from `screening_data.clinical_decision.referral_recommended` (`true`, `false`, or `"not_determined"`).
- **Urgency Tier**: Displayed strictly from `screening_data.clinical_decision.urgency` (`"urgent"`, `"prompt"`, `"routine"`, `"annual_screening"`, `"recapture_required"`, `"manual_review"`).
- **Clinician Guidance / Timeframes**: Displayed strictly from `screening_data.clinical_decision.action_required` and `rationale`. The frontend does not invent or alter clinical consultation windows.

---

## 5. Corrected Contrast Calculations Table

Calculated with mathematical relative luminance ($L$) on `#131C2E` ($L = 0.0117$) and `#090D16` ($L = 0.0063$):

| Color Token | HEX Code | Rel. Lum ($L$) | Exact CR vs `#131C2E` | Exact CR vs `#090D16` | Standard Tested | Result |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **`--eyeris-text-primary`** | `#F8FAFC` | 0.9536 | **16.28:1** | **18.57:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **`--eyeris-text-secondary`**| `#94A3B8` | 0.3595 | **6.64:1** | **7.58:1** | WCAG 1.4.3 Normal Text | **Passes AA** ($\ge 4.5:1$) |
| **`--eyeris-text-muted`** | `#8493A8` | 0.2860 | **5.45:1** | **6.22:1** | WCAG 1.4.3 Normal Text | **Passes AA** ($\ge 4.5:1$) |
| **`--eyeris-primary-btn`** | `#2563EB` | 0.1537 | **3.29:1** | **3.73:1** | WCAG 1.4.11 UI Boundary | **Passes AA Component** ($\ge 3.0:1$)|
| *White Text on #2563EB* | `#FFFFFF` | 1.0000 | **5.17:1** (vs #2563EB) | — | WCAG 1.4.3 Normal Text | **Passes AA** ($\ge 4.5:1$) |
| **`--eyeris-border-focus`** | `#3B82F6` | 0.2355 | **4.63:1** | **5.28:1** | WCAG 1.4.11 Focus Indicator | **Passes AA Component** ($\ge 3.0:1$)|
| **Grade 0 Badge Text** | `#6EE7B7` | 0.6389 | **11.17:1** | **12.75:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 1 Badge Text** | `#67E8F9` | 0.6744 | **11.75:1** | **13.40:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 2 Badge Text** | `#FCD34D` | 0.6782 | **11.81:1** | **13.48:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 3 Badge Text** | `#FDBA74` | 0.5726 | **10.10:1** | **11.52:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 4 Badge Text** | `#FCA5A5` | 0.5032 | **8.97:1** | **10.24:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **Uncertainty Alert Text**| `#C4B5FD` | 0.5188 | **9.22:1** | **10.52:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **Recapture Alert Text** | `#FECACA` | 0.6758 | **11.77:1** | **13.43:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |
| **Model Offline Text** | `#FEF08A` | 0.8523 | **14.63:1** | **16.70:1** | WCAG 1.4.3 Normal Text | **Passes AAA** ($\ge 7.0:1$) |

---

## 6. Remaining Downstream Blockers (Non-Blocking for Design Approval)

1. **Member 1 (Classifier Weights)**: EfficientNet-B0 `.pth` weights remain unharvested. UI safely renders State A (`pending_review`).
2. **Member 2 (Segmentation Weights)**: U-Net lesion `.pth` weights remain unharvested. UI safely hides lesion toggles or marks them as unavailable.
3. **Member 3 (Calibration Parameters)**: Temperature scaling and Platt calibration matrices pending. Epistemic uncertainty displayed as provisional range.
4. **PostgreSQL Service**: Local database offline on port 5432. Health indicator dynamically reports degraded status.

---

## 7. Final Verification & Approval Gate

```
================================================================================
APPROVAL GATE STATUS: AWAITING MEMBER 4 DESIGN IMPLEMENTATION APPROVAL
================================================================================
All clinical decision states, state precedence rules, exact contrast metrics,
and illustrative data labeling have been strictly resolved and synchronized.
No UI code has been implemented, no packages installed, and no Git commits made.
================================================================================
```

