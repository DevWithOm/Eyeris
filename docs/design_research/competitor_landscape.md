# EYERIS — Medical AI & Ophthalmology Competitor Landscape Report
**Subsystem**: UI/UX Research & Design Architecture  
**Role**: Senior Software Architect & Lead Integration Engineer (Member 4)  
**Project**: EYERIS — Explainable AI-Powered Diabetic Retinopathy Screening System (SIH PS26038)  
**Date**: November 2026  
**Status**: Formal Research Deliverable  

---

## 1. Executive Summary

This competitor and market landscape report conducts a rigorous design audit of commercial, clinical, and open-source medical AI products, ophthalmology imaging systems, and clinical SaaS dashboards. The audit examines real-world deployment data from FDA-cleared autonomous screening engines (Digital Diagnostics LumineticsCore, Eyenuk EyeArt), high-volume public health initiatives (Google Health ARDA), CE-marked diagnostic decision-support platforms (Thirona RetCAD), medical device PACS platforms (Topcon Harmony, Carl Zeiss FORUM), and open standard diagnostic medical viewers (OHIF Viewer).

The objective is to establish evidence-based design decisions for the **EYERIS** user interface, ensuring it fulfills the operational requirements of three primary user personas:
1. **Screening Operators / Nurses / Community Health Workers** in rural outreach camps and primary healthcare centers (PHCs).
2. **Consulting Ophthalmologists & Retinal Specialists** reviewing escalated and uncertain cases.
3. **Public Health & Clinic Administrators** monitoring screening throughput, prevalence metrics, and care pathways.

---

## 2. In-Depth Product Evaluations

### 2.1 LumineticsCore (formerly IDx-DR) — Digital Diagnostics
- **Organization**: Digital Diagnostics (Coralville, IA, USA)
- **Regulatory Status**: First FDA-cleared autonomous AI diagnostic system (De Novo 2018; CPT 92229).
- **Target Audience**: Primary care providers, medical assistants, endocrinology nurses without specialized eye-care training.
- **Verified Clinical Workflow**:
  1. Operator logs or pulls patient EHR record into the local client.
  2. Fundus camera captures 2 standard fields (macula-centered and optic disc-centered) per eye.
  3. Local software executes instantaneous quality filtering. If an image is ungradable (due to blur, eyelashes, or inadequate pupil dilation), the system immediately prompts a retake while the patient is still seated.
  4. Image files are encrypted and processed in the cloud (`IDx-Service`) within $\approx 30$ seconds.
  5. The output surfaces a binary clinical triage decision: *"More than mild diabetic retinopathy detected — Refer immediately"* vs. *"Negative for more than mild diabetic retinopathy — Rescreen in 12 months"*.
- **UI/UX Strengths**:
  - *Extremely Low Cognitive Friction*: Zero ambiguous sliders or complex grading metrics shown to non-specialists; output directly dictates clinical next steps.
  - *Immediate In-Chair Feedback Loop*: Prevents patients from leaving the clinic before technical adequacy is verified, eliminating costly patient recall visits.
- **UI/UX Weaknesses & Limitations**:
  - *Black-Box Diagnostic Output*: Provides no visual lesion localization, segmentation, or Grad-CAM attention heatmaps, creating distrust among consulting ophthalmologists when reviewing false positives or edge cases.
  - *Rigid Binary Output*: Does not display ICDR 5-class severity progression (0–4) or calibrated probability scores.
- **Key Takeaways for EYERIS**:
  - Implement an immediate, non-blocking **Image Quality Gate** that prevents ungradable image submission.
  - Provide a simplified "Operator Mode" with high-level referral recommendations while preserving an "Ophthalmologist Mode" with granular AI explainability.

---

### 2.2 EyeArt — Eyenuk
- **Organization**: Eyenuk, Inc. (Los Angeles, CA, USA)
- **Regulatory Status**: FDA 510(k) cleared, CE-marked (Class IIa).
- **Target Audience**: Primary care physicians, diabetes clinics, optometrists.
- **Verified Clinical Workflow**:
  1. Operates on local PC connected to tabletop non-mydriatic cameras (Canon CR-2, Topcon NW400).
  2. Captures two 45° fields per eye (disc and fovea).
  3. Provides live visual feedback on pupil centering and focus.
  4. Cloud-based analysis generates a formal multi-page screening report in $<60$ seconds.
  5. Differentiates between *More-than-Mild DR (mtmDR)* and *Vision-Threatening DR (vtDR)* including Diabetic Macular Edema (DME) risk.
- **UI/UX Strengths**:
  - *Bilateral Separation*: Clean visual partitioning between Right Eye (OD) and Left Eye (OS), matching clinical chart conventions.
  - *Condition Tiering*: Distinguishes between routine referral (mtmDR) and urgent sight-threatening referral (vtDR).
- **UI/UX Weaknesses & Limitations**:
  - *Heavy PDF Report Paradigm*: Results are primarily delivered as printable PDF documents rather than interactive web-native canvases with zoomable lesion overlays.
  - *Network Latency Dependency*: Rural clinics with intermittent cellular connectivity suffer turnaround delays.
- **Key Takeaways for EYERIS**:
  - Enforce bilateral Left/Right eye structure across the screening dashboard.
  - Distinguish between routine ophthalmology referral (Grades 2–3) and sight-threatening urgent escalation (Grade 4 / PDR).
  - Design a lightweight, print-ready screening report view with automated QR/case verification codes.

---

### 2.3 ARDA (Automated Retinal Disease Assessment) — Google Health
- **Organization**: Google Health / Verily (Mountain View, CA, USA)
- **Partners**: Aravind Eye Care System (India), Rajavithi Hospital (Thailand), Lions Outback Vision (Australia).
- **Target Audience**: High-volume rural screening camp operators, general practitioners, regional ophthalmologists.
- **Verified Clinical Workflow**:
  1. High-throughput mobile camps screen hundreds of diabetic patients daily.
  2. Local technician captures fundus photo using portable or desktop fundus cameras (Forus 3nethra, Aurolab).
  3. Image quality model evaluates sharpness, exposure, and field coverage in real time.
  4. Deep learning ensemble evaluates 5-class ICDR grade and referability.
  5. Case is triaged: normal cases receive annual recall notices; referable or ungradable cases are routed to tele-ophthalmology reading centers for remote confirmation.
- **UI/UX Strengths**:
  - *Frontline High-Volume Optimization*: Streamlined form inputs minimizing manual keystrokes in busy community clinics.
  - *Trust Calibration*: High negative predictive value ($>98\%$) clearly communicated to clinicians to safely rule out healthy patients.
  - *Hardware Agnostic / White-Label*: Seamlessly embeddable into third-party camera software.
- **UI/UX Weaknesses & Limitations**:
  - Early field studies showed operators frequently overrode quality warnings due to time pressure in crowded rural camps.
  - Lack of standardized uncertainty indicators caused technician confusion when the model encountered non-diabetic pathologies (e.g. age-related macular degeneration or myopic tessellation).
- **Key Takeaways for EYERIS**:
  - Clearly display model uncertainty and abstain from automated decisions when confidence is borderline ($>0.35$ uncertainty score).
  - Keep the screening upload flow to fewer than three clicks.

---

### 2.4 RetCAD — Thirona
- **Organization**: Thirona (Nijmegen, Netherlands)
- **Integration**: NIDEK NAVIS-EX, iCare ILLUME, Topcon Harmony.
- **Regulatory Status**: CE-marked (MDR Class IIa).
- **Target Audience**: Ophthalmologists, retinal imaging specialists, screening centers.
- **Verified Clinical Workflow**:
  1. Fully integrated into ophthalmology PACS/camera suites.
  2. Generates quantitative risk scores for both Diabetic Retinopathy and Age-Related Macular Degeneration (AMD).
  3. Central viewport renders the retinal fundus image with toggleable AI heatmap overlays highlighting microaneurysms, hemorrhages, and hard/soft exudates.
  4. Right sidebar displays continuous severity scores alongside ICDR classification stages.
- **UI/UX Strengths**:
  - *Diagnostic Transparency & Explainability*: Clinicians can visually inspect the exact retinal regions triggering the AI score, dramatically accelerating verification.
  - *Layered Visualization*: Allows toggling heatmaps on/off and adjusting opacity over the original fundus image.
- **UI/UX Weaknesses & Limitations**:
  - *High Visual Complexity*: Cluttered for community health workers or non-physicians who need actionable referral guidance rather than complex probability curves.
  - *Requires High-End Diagnostic Displays*: Calibrated for darkened ophthalmology reading suites.
- **Key Takeaways for EYERIS**:
  - Adopt RetCAD's **central interactive viewport** with an opacity-controlled Grad-CAM heatmap overlay.
  - Provide interactive lesion segmentation mask toggles (Hard Exudates, Hemorrhages, Microaneurysms).

---

### 2.5 OHIF Viewer & Cornerstone3D (Open Health Imaging Foundation)
- **Organization**: Open-source consortium (Massachusetts General Hospital, Radical Imaging).
- **Platform**: Web-based DICOM/PACS viewer utilizing HTML5 Canvas, WebGL, and Cornerstone3D.
- **Target Audience**: Radiologists, tele-ophthalmologists, clinical researchers.
- **Verified UI/UX Characteristics**:
  - *Diagnostic Reading Room Theme*: High-contrast deep slate/charcoal dark mode (`#0f172a`, `#1e293b`) designed to eliminate glare and maximize human retinal contrast sensitivity.
  - *Configurable Multi-Viewport Grids*: $1\times1$, $1\times2$ (side-by-side comparative), $2\times2$ grids.
  - *Precision Viewport Tools*: Window/Level (brightness/contrast), interactive pan/zoom, linear pixel calibration, ROI measurement.
- **UI/UX Strengths**:
  - Gold standard for clinical web image ergonomics, keyboard navigation shortcuts, and cross-platform zero-footprint rendering.
- **UI/UX Weaknesses & Limitations**:
  - Pure diagnostic viewing tool with no built-in patient intake, screening triage, or population health analytics.
- **Key Takeaways for EYERIS**:
  - Implement a dedicated **Clinical Dark Mode / Inspection Mode** for the fundus viewer viewport to ensure optimal visualization of subtle microaneurysms and faint hemorrhages.
  - Provide synchronized side-by-side comparison (Original Fundus vs. Grad-CAM / Lesion Mask).

---

### 2.6 Modern Clinical Healthcare SaaS (Epic Cheers / Cerner / Aidoc / Viz.ai)
- **Product Domain**: Acute care AI triage dashboards and enterprise EHR systems.
- **Verified UI/UX Patterns**:
  - *Triage Queue Priority Styling*: Color-coded status badges with high WCAG AA contrast (Red = Critical/Sight-threatening, Amber = Moderate Review, Green = Within Normal Limits, Slate = Pending Quality).
  - *Audit Logging & Attribution*: Every automated finding displays algorithm version, timestamp, and explicit disclaimer badge.
- **Key Takeaways for EYERIS**:
  - Use high-contrast, universally recognizable clinical color tokens.
  - Prominently feature the mandatory regulatory research disclaimer without occluding primary diagnostic content.

