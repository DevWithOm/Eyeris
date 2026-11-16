# EYERIS — Final Visual Design System & Token Specification (Revision 2)
**Subsystem**: UI/UX Design System  
**Role**: Senior Healthcare UX Architect & Design Systems Lead (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 16, 2026  
**Status**: Revised Specification Incorporating Final Safety & Accessibility Audit  

---

## 1. Member 4 Approved Design Decisions (Revision 2 Final)

This revised design system incorporates the following twelve audited decisions:
1. Standardizes on the Diagnostic Slate Dark Palette (`#090D16` root canvas, `#131C2E` elevated card surface).
2. Preserves Inter typography with tabular numerals (`tnum`) for layout stability across numeric telemetry.
3. Incorporates exact, mathematically verified contrast ratios derived from the official WCAG relative-luminance formula.
4. Corrects previously misstated contrast values for `#3B82F6` (4.63:1 non-text focus indicator against surface), `#67E8F9` (11.75:1), and `#FEF08A` (14.63:1).
5. Standardizes primary button backgrounds on `#2563EB` (luminance 0.1537) to guarantee **5.17:1** contrast with white text (`#FFFFFF`), resolving the 3.68:1 text failure of `#3B82F6`.
6. Enforces multi-channel accessibility: clinical severity and system statuses are never conveyed through color alone; every indicator combines an icon shape, a text label, and a numeric stage.
7. Elevates the dual-pane retinal analysis workspace as the primary visual and technical showcase.
8. Guarantees raw anatomical fundus visibility through continuous opacity adjustment ($0–100\%$) and a spacebar bypass.
9. Enforces role-aware presentation modes (Operator View vs. Specialist View) that consume the identical backend contract without modifying the decision engine.
10. Separates pipeline states into four distinct UI representations with strict precedence: Quality Failure (Priority 1), Model Unavailable (Priority 2), Model Uncertainty (Priority 3), and Referral Decision (Priority 4).
11. Treats quality (0.60) and uncertainty (0.35) thresholds as configurable provisional engineering values, not certified clinical standards.
12. Labels all wireframe metrics as illustrative examples and explicitly disclaims regulatory clearance.

---

## 2. Reproducible Mathematical WCAG 2.2 Contrast Verification

### 2.1 WCAG Relative Luminance Formula
For each sRGB color component $C \in \{R, G, B\}$ normalized to $[0, 1]$:
$$C_{\text{linear}} = \begin{cases} \frac{C}{12.92} & \text{if } C \le 0.04045 \\ \left(\frac{C + 0.055}{1.055}\right)^{2.4} & \text{if } C > 0.04045 \end{cases}$$
$$\text{Relative Luminance } L = 0.2126 \cdot R_{\text{linear}} + 0.7152 \cdot G_{\text{linear}} + 0.0722 \cdot B_{\text{linear}}$$
$$\text{Contrast Ratio } CR = \frac{L_{\text{lighter}} + 0.05}{L_{\text{darker}} + 0.05}$$

- **Canvas Background (`#090D16`)**: $L = 0.0063$
- **Surface-1 Background (`#131C2E`)**: $L = 0.0117$

---

### 2.2 Complete Contrast Verification Table

| Color Role | HEX Code | Rel. Lum ($L$) | Exact CR vs Surface (`#131C2E`) | Exact CR vs Canvas (`#090D16`) | Applicable WCAG Standard | Compliance Status |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **`--eyeris-text-primary`** | `#F8FAFC` | 0.9536 | **16.28:1** | **18.57:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **`--eyeris-text-secondary`**| `#94A3B8` | 0.3595 | **6.64:1** | **7.58:1** | WCAG 1.4.3 Text (Normal) | **Passes AA** ($\ge 4.5:1$) |
| **`--eyeris-text-muted`** | `#8493A8` | 0.2860 | **5.45:1** | **6.22:1** | WCAG 1.4.3 Text (Normal) | **Passes AA** ($\ge 4.5:1$) |
| **`--eyeris-primary-btn`** | `#2563EB` | 0.1537 | **3.29:1** | **3.73:1** | WCAG 1.4.11 Component | **Passes AA Component** ($\ge 3.0:1$)|
| *Btn Text on #2563EB* | `#FFFFFF` | 1.0000 | **5.17:1** (vs #2563EB) | — | WCAG 1.4.3 Text (Normal) | **Passes AA** ($\ge 4.5:1$) |
| **`--eyeris-border-focus`** | `#3B82F6` | 0.2355 | **4.63:1** | **5.28:1** | WCAG 1.4.11 Focus Indicator | **Passes AA Component** ($\ge 3.0:1$)|
| **`--eyeris-border-strong`**| `#2E4366` | 0.0555 | **1.71:1** | **1.95:1** | Structural Boundary | Decorative Inset |
| **`--eyeris-border-subtle`**| `#1E2C44` | 0.0249 | **1.22:1** | **1.39:1** | Structural Boundary | Decorative Divider |
| **Grade 0 Badge Text** | `#6EE7B7` | 0.6389 | **11.17:1** | **12.75:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 1 Badge Text** | `#67E8F9` | 0.6744 | **11.75:1** | **13.40:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 2 Badge Text** | `#FCD34D` | 0.6782 | **11.81:1** | **13.48:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 3 Badge Text** | `#FDBA74` | 0.5726 | **10.10:1** | **11.52:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **Grade 4 Badge Text** | `#FCA5A5` | 0.5032 | **8.97:1** | **10.24:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **Uncertainty Alert Text**| `#C4B5FD` | 0.5188 | **9.22:1** | **10.52:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **Recapture Alert Text** | `#FECACA` | 0.6758 | **11.77:1** | **13.43:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |
| **Model Offline Text** | `#FEF08A` | 0.8523 | **14.63:1** | **16.70:1** | WCAG 1.4.3 Text (Normal) | **Passes AAA** ($\ge 7.0:1$) |

*Distinction Note*: Text contrast (WCAG 1.4.3) requires $\ge 4.5:1$ for normal body text and $\ge 3.0:1$ for large text ($>18$pt or $>14$pt bold). Non-text component contrast (WCAG 1.4.11) requires $\ge 3.0:1$ for visual boundaries of active user interface components and focus indicators.

---

## 3. Multi-Channel Status Encoding (WCAG 1.4.1)

Color is never the sole communicator of clinical urgency or system health:

```
+---------------------------------------------------------------------------------------------------------+
|                                    MULTI-CHANNEL CLINICAL STATUS ENCODING                               |
+--------------------------+-------------+---------------+-----------------------+------------------------+
| Status State             | Icon Shape  | Color Code    | Explicit Text Label   | Numeric / System Code  |
+--------------------------+-------------+---------------+-----------------------+------------------------+
| Grade 0 (No DR)          | Circle  [●] | Green #10B981 | "Grade 0: No DR"      | ICDR Stage 0           |
| Grade 1 (Mild NPDR)      | Square  [■] | Cyan  #06B6D4 | "Grade 1: Mild NPDR"  | ICDR Stage 1           |
| Grade 2 (Moderate NPDR)  | Diamond [◆] | Amber #F59E0B | "Grade 2: Mod NPDR"   | ICDR Stage 2           |
| Grade 3 (Severe NPDR)    | Triangle[▲] | Orange#F97316 | "Grade 3: Severe NPDR"| ICDR Stage 3           |
| Grade 4 (Proliferative)  | Octagon [⯄] | Red   #EF4444 | "Grade 4: PDR"        | ICDR Stage 4           |
| Model Uncertainty Gate   | Shield  [🛡] | Violet#8B5CF6 | "High Uncertainty"    | Status: Not determined |
| Image Quality Rejection  | Warning [⚠] | Red   #DC2626 | "Recapture Required"  | Quality Score < 0.60   |
| Model Unavailable State  | Pause   [⏸] | Yellow#EAB308 | "Manual Review"       | Status: pending_review |
+--------------------------+-------------+---------------+-----------------------+------------------------+
```

---

## 4. Typography System & Numerical Precision

- **Font Family**: `Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Tabular Numerals**: `font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1;` strictly enforced on all telemetry, coordinates, and case identifiers.
- **Scale**:
  - `Display / H1`: 28px (1.75rem), Bold (700), Line-height 1.2
  - `Section / H2`: 20px (1.25rem), Semibold (600), Line-height 1.3
  - `Card Header / H3`: 16px (1.00rem), Semibold (600), Line-height 1.4
  - `Body Standard`: 14px (0.875rem), Regular (400), Line-height 1.45
  - `Table Data`: 13px (0.8125rem), Medium (500), Monospace `tnum`
  - `Caption / Badge`: 12px (0.75rem), Semibold (600), Uppercase tracking +0.05em
  - `Legal Disclaimer`: 11px (0.6875rem), Regular (400), Italic, `#8493A8`

---

## 5. Master Layout Dimensions & Responsive Grid

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
