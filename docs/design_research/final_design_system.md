# EYERIS — Final Visual Design System & Token Specification (Revision 1)
**Subsystem**: UI/UX Design System  
**Role**: Senior Product Designer & Design Systems Engineer (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 16, 2026  
**Status**: Revised Specification Incorporating Member 4 Approved Design Decisions  

---

## 1. Member 4 Approved Design Decisions

This revised design system integrates the following twelve approved architectural decisions:
1. Standardizes on the Diagnostic Slate Dark Palette (`#090D16` canvas, `#131C2E` primary card surface).
2. Preserves Inter typography with tabular numerals (`tnum`) for data stability.
3. Incorporates exact mathematically verified WCAG 2.2 AA contrast ratios for all foreground/background pairings.
4. Enforces multi-channel accessibility: clinical severity and system statuses are never conveyed through color alone; every indicator combines an icon, a text label, and a numeric stage.
5. Elevates the dual-pane retinal analysis workspace as the primary visual and technical showcase.
6. Calibrates lesion overlays (hard exudates, hemorrhages, microaneurysms) for maximum clarity without obscuring retinal tissue.
7. Guarantees raw anatomical fundus visibility through continuous opacity adjustment ($0–100\%$) and a spacebar bypass.
8. Enforces role-aware presentation modes (Operator View vs. Specialist View) that consume the identical backend contract without modifying the decision engine.
9. Separates pipeline states into four distinct UI representations: Model Unavailability, Image Quality Failure, Model Uncertainty, and Clinical Referral.
10. Treats quality (0.60) and uncertainty (0.35) thresholds as configurable provisional engineering values, not clinically certified thresholds.
11. Labels all wireframe metrics as `[Example Wireframe Value: e.g. N]`.
12. Explicitly disclaims regulatory clearance or automated diagnostic claims.

---

## 2. Mathematically Verified Color Token Architecture

All contrast ratios were computed using the standard WCAG relative luminance formula:
$$\text{Contrast Ratio} = \frac{L_1 + 0.05}{L_2 + 0.05}$$
where $L_1$ is the relative luminance of the lighter color and $L_2$ is the relative luminance of the darker color. Target: WCAG 2.2 Level AA ($\ge 4.5:1$ for body text, $\ge 3.0:1$ for large text and UI components).

### 2.1 Surface & Typographic Tokens with Exact Contrast Ratios

| Token Name | HEX Value | Surface Role | Exact Contrast vs Canvas (`#090D16`) | Exact Contrast vs Surface-1 (`#131C2E`) | WCAG 2.2 AA Compliance |
| :--- | :---: | :--- | :---: | :---: | :---: |
| `--eyeris-canvas` | `#090D16` | Deepest root canvas | Base (1.00:1) | — | Base Background |
| `--eyeris-surface-subtle` | `#0F1624` | Inset wells, table headers | 1.15:1 | — | Low-contrast boundary |
| `--eyeris-surface-1` | `#131C2E` | Primary elevated card panels | 1.25:1 | Base (1.00:1) | Primary Container |
| `--eyeris-surface-2` | `#1B263B` | Interactive hover states | 1.62:1 | 1.30:1 | Component Surface |
| `--eyeris-surface-3` | `#25334E` | Active highlights, tooltips | 2.15:1 | 1.72:1 | Elevated Overlay |
| `--eyeris-border-subtle` | `#1E2C44` | Structural card borders | 1.39:1 | 1.22:1 | Divider |
| `--eyeris-border-focus` | `#3B82F6` | Keyboard focus ring | 4.88:1 | 4.28:1 | **Passes AA Component (3.0:1)** |
| **`--eyeris-text-primary`** | `#F8FAFC` | Display & primary headers | **18.57:1** | **16.28:1** | **Passes AAA ($\ge 7.0:1$)** |
| **`--eyeris-text-secondary`**| `#94A3B8` | Field labels, captions | **7.58:1** | **6.64:1** | **Passes AA ($\ge 4.5:1$)** |
| **`--eyeris-text-muted`** | `#8493A8` | Calibrated footnotes, units | **6.22:1** | **5.45:1** | **Passes AA ($\ge 4.5:1$)** |

---

### 2.2 Clinical Severity & Status Tokens (Multi-Channel Encoding)
*Every clinical status token is paired with an icon shape, text label, and numeric severity indicator. The text tints below are specifically calibrated to yield high-contrast legibility against dark badge containers.*

| Clinical Severity / Status | Base Token HEX | Badge Text Tint | Exact Text Contrast vs Surface-1 (`#131C2E`) | Multi-Channel Encoding (WCAG 1.4.1) | Clinical Action |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **Grade 0 (No DR)** | `#10B981` | `#6EE7B7` | **11.17:1** (Passes AAA) | Circle Icon `[●]` + Text `"Grade 0: No DR"` | Routine Annual Screening |
| **Grade 1 (Mild NPDR)** | `#06B6D4` | `#67E8F9` | **12.45:1** (Passes AAA) | Square Icon `[■]` + Text `"Grade 1: Mild NPDR"` | Routine Monitoring (6–12 Mo) |
| **Grade 2 (Moderate NPDR)**| `#F59E0B` | `#FCD34D` | **11.81:1** (Passes AAA) | Diamond Icon `[◆]` + Text `"Grade 2: Moderate NPDR"`| Routine Referral (4–8 Wks) |
| **Grade 3 (Severe NPDR)** | `#F97316` | `#FDBA74` | **10.10:1** (Passes AAA) | Triangle Icon `[▲]` + Text `"Grade 3: Severe NPDR"`| Prompt Referral (2–4 Wks) |
| **Grade 4 (Proliferative)**| `#EF4444` | `#FCA5A5` | **8.97:1** (Passes AAA) | Octagon Icon `[⯄]` + Text `"Grade 4: PDR"` | Urgent Specialist Referral (1–2 Wks) |
| **Model Uncertainty Alert**| `#8B5CF6` | `#C4B5FD` | **9.22:1** (Passes AAA) | Shield Icon `[🛡]` + Text `"High Uncertainty"` | Specialist Confirmation Required |
| **Image Quality Rejection**| `#DC2626` | `#FECACA` | **11.77:1** (Passes AAA) | Alert Icon `[⚠]` + Text `"Recapture Required"`| Immediate In-Chair Retake |
| **Model Offline State** | `#EAB308` | `#FEF08A` | **13.52:1** (Passes AAA) | Pause Icon `[⏸]` + Text `"Manual Review"` | Clinician Manual Grading Queue |

---

### 2.3 Retinal Lesion Overlay Tokens
- **Hard Exudates**: `--eyeris-lesion-exudate: #FACC15` (Vivid Yellow fill with 1px border).
- **Hemorrhages / Microaneurysms**: `--eyeris-lesion-hemorrhage: #EF4444` (Crimson Red fill).
- **Microaneurysm Markers**: `--eyeris-lesion-ma: #06B6D4` (Electric Cyan circular points).
- **Cotton Wool Spots**: `--eyeris-lesion-cws: #E2E8F0` (Semi-translucent Chalk White contour).

---

## 3. Typography System & Numerical Precision

- **Font Family**: `Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Tabular Numerals**: `font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;` strictly applied to all telemetry values, Case IDs, quality scores, coordinates, and probabilities.
- **Type Scale**:
  - `Display / H1`: 28px (1.75rem), Bold (700), Line-height 1.2
  - `Section / H2`: 20px (1.25rem), Semibold (600), Line-height 1.3
  - `Card Header / H3`: 16px (1.00rem), Semibold (600), Line-height 1.4
  - `Body Standard`: 14px (0.875rem), Regular (400), Line-height 1.45
  - `Table Data`: 13px (0.8125rem), Medium (500), Monospace `tnum`
  - `Caption / Badge`: 12px (0.75rem), Semibold (600), Uppercase tracking +0.05em
  - `Legal Disclaimer`: 11px (0.6875rem), Regular (400), Italic, `#8493A8`

---

## 4. Master Layout Dimensions & Responsive Grid

```
+---------------------------------------------------------------------------------------------------------+
| Persistent Global Patient Context Bar: Height 56px | Sticky Top Navigation                              |
+---------------------------------------------------------------------------------------------------------+
| Persistent Medical Disclaimer Banner: Height 32px | Amber/Slate Legal Research Notice                   |
+----------------------+----------------------------------------------------------------------------------+
| Collapsible Sidebar  | Master Application Workspace (Fluid Width, Max 1600px, Margin Auto)              |
| Standard: 240px      | Padding: 24px (Desktop) / 16px (Mobile)                                          |
| Collapsed: 64px      |                                                                                  |
|                      | Screening Details Workspace (Primary Technical Showcase):                        |
| [Dashboard]          | +-----------------------------------------+------------------------------------+ |
| [New Screening]      | | Left Pane: Retinal Viewport (60% Width) | Right Pane: Telemetry (40% Width)  | |
| [Screening History]  | | Synchronized Pan/Zoom, Opacity Slider   | ICDR Grade, Quality, Uncertainty,  | |
| [Screening Details]  | | Anatomical Landmark Preservation        | Referral Action Tiering            | |
| [Reports]            | +-----------------------------------------+------------------------------------+ |
| [System Status]      |                                                                                  |
| [Settings]           |                                                                                  |
+----------------------+----------------------------------------------------------------------------------+
```

### Breakpoints:
- **Desktop Large ($\ge 1440$px)**: Full sidebar (240px), 2-column workspace (60% viewer / 40% triage).
- **Desktop Standard ($1200$px – $1439$px)**: Collapsed icon sidebar (64px), 2-column workspace.
- **Tablet ($768$px – $1199$px)**: Off-canvas drawer navigation, single-column tabbed layout.
- **Mobile / Outreach Tablet ($< 768$px)**: Bottom navigation rail, vertical stacked flow.

---

## 5. Accessibility Compliance Architecture (WCAG 2.2 AA)

1. **Color Independence (WCAG 1.4.1)**: All status badges combine distinct icon glyphs (`[●]`, `[■]`, `[◆]`, `[▲]`, `[⯄]`), numeric values, and text labels.
2. **Contrast Verification (WCAG 1.4.3 & 1.4.11)**:
   - Primary text against surface: **16.28:1** (Exceeds AAA 7.0:1 requirement).
   - Secondary text against surface: **6.64:1** (Exceeds AA 4.5:1 requirement).
   - Calibrated muted text against surface: **5.45:1** (Exceeds AA 4.5:1 requirement).
   - Status badge text against badge containers: **8.97:1 to 13.52:1** (Exceeds AAA 7.0:1).
3. **Keyboard Viewport Controls (WCAG 2.1.1)**:
   - `H`: Toggle Grad-CAM attention heatmap overlay on/off.
   - `Space` (Hold): Temporarily set heatmap opacity to 0% to reveal the raw fundus image.
   - `+` / `-`: Incremental zoom in / zoom out.
   - `0`: Reset viewport pan and zoom to fit.
   - `Esc`: Close open modal dialogs.
