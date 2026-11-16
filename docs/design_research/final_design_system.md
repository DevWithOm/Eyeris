# EYERIS — Final Visual Design System & Token Specification
**Subsystem**: UI/UX Design System  
**Role**: Senior Product Designer & Design Systems Engineer (Member 4)  
**Project**: EYERIS — Explainable AI Diabetic Retinopathy Screening System  
**Date**: November 2026  
**Status**: Proposal for Design Approval Gate  

---

## 1. Design Token Architecture & CSS Root Definitions

All design tokens are structured as CSS custom properties with strict semantic naming conventions, calibrated for high-contrast accessibility (WCAG 2.2 AA compliant, targeting AAA where applicable) against diagnostic dark surfaces.

```css
:root {
  /* =========================================================================
     1. CANVAS & SURFACE ELEVATION (Diagnostic Dark Slate Palette)
     Rationale: Avoids pure pitch black (#000000) which causes harsh OLED halation,
     and bright white (#FFFFFF) which constricts pupils during retinal examination.
     ========================================================================= */
  --eyeris-canvas: #090d16;          /* Deepest root background canvas */
  --eyeris-surface-subtle: #0f1624;  /* Inset wells, table headers, code blocks */
  --eyeris-surface-1: #131c2e;       /* Level 1: Primary card panels & modals */
  --eyeris-surface-2: #1b263b;       /* Level 2: Interactive elements, hover states */
  --eyeris-surface-3: #25334e;       /* Level 3: Active tabs, tooltips, popovers */

  /* Borders & Dividers */
  --eyeris-border-subtle: #1e2c44;   /* Default card divider (4.8:1 contrast on canvas) */
  --eyeris-border-strong: #2e4366;   /* Active boundaries, input borders */
  --eyeris-border-focus: #3b82f6;    /* Visible keyboard focus ring (WCAG 2.4.7) */

  /* =========================================================================
     2. TYPOGRAPHIC COLOR TOKENS
     ========================================================================= */
  --eyeris-text-primary: #f8fafc;    /* Headings, primary metrics, active text (15.2:1) */
  --eyeris-text-secondary: #94a3b8;  /* Labels, table data, subheadings (6.5:1) */
  --eyeris-text-muted: #64748b;      /* Disabled text, metadata footnotes (4.6:1) */
  --eyeris-text-inverse: #090d16;    /* Dark text for use on bright badges */

  /* =========================================================================
     3. CLINICAL SEVERITY & STATUS TOKENS (ICDR 5-Grade Scale)
     Note: Colors are NEVER used as the sole conveyor of information (WCAG 1.4.1).
     Every status token is paired with an icon, numeric grade, and text label.
     ========================================================================= */
  --eyeris-grade-0: #10b981;         /* Grade 0 - No DR: Emerald Green (Annual Screen) */
  --eyeris-grade-1: #06b6d4;         /* Grade 1 - Mild: Cyan (Routine Monitoring) */
  --eyeris-grade-2: #f59e0b;         /* Grade 2 - Moderate: Amber (Routine Referral) */
  --eyeris-grade-3: #f97316;         /* Grade 3 - Severe: Orange (Prompt Referral) */
  --eyeris-grade-4: #ef4444;         /* Grade 4 - Proliferative: Crimson (Urgent Referral) */

  /* Functional Triage States */
  --eyeris-status-urgent: #ef4444;   /* Urgent Referral required */
  --eyeris-status-routine: #10b981;  /* Routine monitoring / healthy */
  --eyeris-status-recapture: #dc2626;/* Quality rejection / Recapture mandatory */
  --eyeris-status-uncertain: #8b5cf6;/* Model uncertainty detected / Escalate */
  --eyeris-status-pending: #eab308;  /* Model pending review / In-flight */

  /* =========================================================================
     4. RETINAL LESION OVERLAY TOKENS
     Calibrated against fundus photography to maximize edge visibility.
     ========================================================================= */
  --eyeris-lesion-exudate: #facc15;   /* Hard Exudates: Vivid yellow */
  --eyeris-lesion-hemorrhage: #ef4444;/* Hemorrhages: High-contrast scarlet red */
  --eyeris-lesion-ma: #06b6d4;        /* Microaneurysms: Electric cyan dot markers */
  --eyeris-lesion-cws: #e2e8f0;       /* Cotton Wool Spots: Translucent chalk white */

  /* =========================================================================
     5. SPATIAL & GEOMETRY TOKENS (8px Base Grid)
     ========================================================================= */
  --eyeris-space-1: 4px;             /* Micro spacer */
  --eyeris-space-2: 8px;             /* Tight spacer, icon-text gap */
  --eyeris-space-3: 12px;            /* Input padding, badge margins */
  --eyeris-space-4: 16px;            /* Standard component padding */
  --eyeris-space-5: 20px;            /* Moderate card spacing */
  --eyeris-space-6: 24px;            /* Card container padding */
  --eyeris-space-8: 32px;            /* Section separation */
  --eyeris-space-12: 48px;           /* Major page grid gap */

  /* Border Radii */
  --eyeris-radius-sm: 4px;           /* Tags, small buttons, status pills */
  --eyeris-radius-md: 6px;           /* Form inputs, select dropdowns */
  --eyeris-radius-lg: 8px;           /* Standard cards, dialogs, viewports */
  --eyeris-radius-xl: 12px;          /* Master layout containers, modals */
  --eyeris-radius-full: 9999px;      /* Circular status dots, avatars */

  /* Elevation Shadows */
  --eyeris-shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2);
  --eyeris-shadow-modal: 0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
  --eyeris-shadow-glow-focus: 0 0 0 3px rgba(59, 130, 246, 0.4);
}
```

---

## 2. Typography System & Type Scale

The typeface is **Inter** (with system-ui fallbacks) for optimal legibility at micro-sizes. All numeric metrics use tabular numeral alignment (`tnum`) to eliminate visual dancing during live data updates.

| Style Role | Font Size | Line Height | Weight | Letter Spacing | CSS Implementation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Display Header** | 28px (1.75rem) | 34px | 700 (Bold) | -0.02em | `font-size: 1.75rem; font-weight: 700; line-height: 1.2;` |
| **Section Header (H1)** | 22px (1.375rem) | 28px | 600 (Semibold) | -0.01em | `font-size: 1.375rem; font-weight: 600; line-height: 1.28;` |
| **Card Header (H2)** | 16px (1.00rem) | 22px | 600 (Semibold) | 0.00em | `font-size: 1.00rem; font-weight: 600; line-height: 1.375;` |
| **Body Standard** | 14px (0.875rem) | 20px | 400 (Regular) | 0.00em | `font-size: 0.875rem; font-weight: 400; line-height: 1.43;` |
| **Body Semibold** | 14px (0.875rem) | 20px | 600 (Semibold) | 0.00em | `font-size: 0.875rem; font-weight: 600; line-height: 1.43;` |
| **Table & Monospace** | 13px (0.8125rem) | 18px | 500 (Medium) | 0.02em | `font-size: 0.8125rem; font-family: monospace; font-variant-numeric: tabular-nums;` |
| **Caption / Badge** | 12px (0.75rem) | 16px | 600 (Semibold) | +0.04em | `font-size: 0.75rem; font-weight: 600; text-transform: uppercase;` |
| **Legal / Disclaimer**| 11px (0.6875rem) | 16px | 400 (Regular) | 0.00em | `font-size: 0.6875rem; color: var(--eyeris-text-muted); font-style: italic;` |

---

## 3. Core Component Library Specifications

### 3.1 Buttons
- **Primary Action**: Solid blue (`#3B82F6`), hover `#2563EB`, active `#1D4ED8`, text `#FFFFFF`. 36px height, 12px horizontal padding, 6px border radius.
- **Secondary Action**: Background `--eyeris-surface-2`, border `1px solid --eyeris-border-strong`, text `--eyeris-text-primary`.
- **Destructive Action**: Background `#EF4444`, hover `#DC2626`, text `#FFFFFF`.
- **Ghost / Icon Button**: Transparent background, hover `--eyeris-surface-2`, text `--eyeris-text-secondary`, 32x32px hit target.
- **Focus States**: High-contrast blue outline (`3px solid rgba(59, 130, 246, 0.6)`), 2px focus offset.

### 3.2 Form Inputs & File Dropzone
- **Text / Select Input**: Height 38px, background `--eyeris-surface-subtle`, border `1px solid --eyeris-border-subtle`, focus border `--eyeris-border-focus`. Tabular numbers for IDs.
- **Fundus Upload Dropzone**:
  - Minimum height: 220px.
  - Border: 2px dashed `--eyeris-border-strong` (transitions to `#3B82F6` solid on dragover).
  - Background: `--eyeris-surface-subtle` with subtle radial camera vignette.
  - Interactive states: Idle, Drag-Hover, Validating, Uploading (progress bar), Error (red dashed), Success (green border + fundus thumbnail).

### 3.3 Cards & Data Containers
- **Diagnostic Card**: Padding 20px, background `--eyeris-surface-1`, border `1px solid --eyeris-border-subtle`, border-radius 8px, shadow `--eyeris-shadow-card`.
- **Triage Alert Banner**: Full width, left 4px solid accent border (e.g. red for urgent referral, amber for manual review, green for annual monitoring), background `--eyeris-surface-1`.

### 3.4 Data Tables
- **Screening Registry Table**:
  - Sticky header with background `--eyeris-surface-subtle` and bottom border `2px solid --eyeris-border-strong`.
  - Row height: 48px, hover background `--eyeris-surface-2`.
  - Column layout: Case ID (monospace), Screening Date/Time, Image Quality Badge, DR Grade Segment, Urgency Badge, Action Button.
  - Sort indicators: Visual up/down arrows with `aria-sort` attributes.

### 3.5 Status Badges & Indicators
- Built with dual visual indicators: a 6px circular glowing status dot + bold text label.
  - **Urgent Referral**: Dot `#EF4444`, text `#FCA5A5`, bg `rgba(239, 68, 68, 0.15)`.
  - **Prompt Referral**: Dot `#F97316`, text `#FDBA74`, bg `rgba(249, 115, 22, 0.15)`.
  - **Routine Referral**: Dot `#F59E0B`, text `#FCD34D`, bg `rgba(245, 158, 11, 0.15)`.
  - **Annual Rescreening**: Dot `#10B981`, text `#6EE7B7`, bg `rgba(16, 185, 129, 0.15)`.
  - **Manual Review**: Dot `#8B5CF6`, text `#C4B5FD`, bg `rgba(139, 92, 246, 0.15)`.
  - **Quality Rejection**: Dot `#DC2626`, text `#FCA5A5`, bg `rgba(220, 38, 38, 0.20)`.

### 3.6 Tooltips & Modals
- **Tooltip**: Background `--eyeris-surface-3`, border `1px solid --eyeris-border-strong`, text `--eyeris-text-primary`, font size 12px, padding 6px 10px, border-radius 4px, z-index 1000.
- **Modal Dialog**: Centered overlay with backdrop blur (`backdrop-filter: blur(4px); background: rgba(9, 13, 22, 0.75)`). Modal box: max-width 560px, padding 24px, background `--eyeris-surface-1`, border `1px solid --eyeris-border-strong`, border-radius 12px.

---

## 4. Master Layout Dimensions & Responsive Grid

```
+---------------------------------------------------------------------------------------------------------+
| Top Header Bar: Height 56px | Persistent Patient Context + Health Status + Mode Switcher                |
+---------------------------------------------------------------------------------------------------------+
| Persistent Disclaimer Banner: Height 32px | Amber/Slate Legal Research Notice                           |
+----------------------+----------------------------------------------------------------------------------+
| Sidebar Navigation   | Main Content Area (Fluid width, Max 1600px, Margin Auto)                         |
| Width: 240px         | Padding: 24px (Desktop) / 16px (Mobile)                                          |
| (Collapsible to 64px)|                                                                                  |
|                      |                                                                                  |
| - Dashboard          |                                                                                  |
| - New Screening      |                                                                                  |
| - Screening History  |                                                                                  |
| - Screening Details  |                                                                                  |
| - Reports            |                                                                                  |
| - System Status      |                                                                                  |
| - Settings           |                                                                                  |
+----------------------+----------------------------------------------------------------------------------+
```

### Breakpoints:
- **Desktop Large ($\ge 1440$px)**: Full sidebar (240px), 2-column details workspace (60% viewer / 40% clinical triage).
- **Desktop Standard ($1200$px – $1439$px)**: Collapsed icon sidebar (64px), 2-column details workspace.
- **Tablet ($768$px – $1199$px)**: Off-canvas drawer sidebar, single-column tabbed layout (Tab 1: Viewport, Tab 2: Clinical Details, Tab 3: Report).
- **Mobile / Outreach Tablet ($< 768$px)**: Bottom navigation bar, vertical stacked flow optimized for one-handed photo review and triage logging.

---

## 5. Accessibility Compliance Architecture (WCAG 2.2 AA)

1. **Color Independence (WCAG 1.4.1)**: Every DR grade and urgency level includes an unambiguous text label, icon shape, and numeric indicator in addition to its color code.
2. **Contrast Ratios (WCAG 1.4.3 & 1.4.11)**:
   - Body text against surface: $\ge 6.5:1$ (exceeds 4.5:1 AA requirement).
   - Headings against surface: $\ge 15.2:1$ (exceeds 7:1 AAA requirement).
   - Interactive borders and focus rings: $\ge 3.2:1$.
3. **Keyboard Navigability (WCAG 2.1.1 & 2.4.7)**:
   - Full tab-index flow across all form inputs and interactive buttons.
   - Dedicated retinal image viewer shortcuts:
     - `H`: Toggle Grad-CAM Heatmap overlay.
     - `Space` (Hold): Temporarily reveal raw fundus photograph.
     - `+` / `-`: Zoom in / Zoom out.
     - `0`: Reset viewport zoom and pan.
     - `Esc`: Close open modal dialogs.
4. **Screen Reader Announcements (WCAG 4.1.2)**:
   - Dynamic image upload states announce via `aria-live="polite"`.
   - Critical quality rejections announce via `aria-live="assertive"` and `role="alert"`.

