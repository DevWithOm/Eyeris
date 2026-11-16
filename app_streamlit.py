"""
Diabetic Retinopathy Screening - Web Prototype (Streamlit).

A clean, professional medical screening dashboard designed for demonstration
and clinical research workflow review.

Features:
- Image upload supporting PNG, JPG, and JPEG.
- Real inference via `ai_models.classification.predict.predict_grade`.
- Display of DR grade (0-4), grade name, raw confidence, and all 5 class probabilities.
- Interactive probability distribution bar chart.
- Clear distinction between raw model confidence and calibrated clinical confidence.
- Graceful error handling and loading indicators.
- Research prototype disclaimer.
"""

from pathlib import Path
import sys
import tempfile

import altair as alt
import pandas as pd
from PIL import Image
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the actual prediction interface
try:
    from ai_models.classification.predict import predict_grade
    from ai_models.common.labels import DR_GRADE_LABELS
except ImportError as e:
    predict_grade = None
    DR_GRADE_LABELS = {
        0: "No DR",
        1: "Mild",
        2: "Moderate",
        3: "Severe",
        4: "Proliferative DR",
    }
    IMPORT_ERROR = str(e)
else:
    IMPORT_ERROR = None

# Page Configuration
st.set_page_config(
    page_title="Eyeris - Diabetic Retinopathy Screening",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for Medical Dashboard
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .disclaimer-banner {
        background-color: #fef3c7;
        border-left: 5px solid #d97706;
        padding: 0.85rem 1.1rem;
        border-radius: 6px;
        color: #92400e;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .grade-badge-0 { color: #166534; background-color: #dcfce7; padding: 4px 12px; border-radius: 12px; font-weight: 700; }
    .grade-badge-1 { color: #854d0e; background-color: #fef9c3; padding: 4px 12px; border-radius: 12px; font-weight: 700; }
    .grade-badge-2 { color: #c2410c; background-color: #ffedd5; padding: 4px 12px; border-radius: 12px; font-weight: 700; }
    .grade-badge-3 { color: #b91c1c; background-color: #fee2e2; padding: 4px 12px; border-radius: 12px; font-weight: 700; }
    .grade-badge-4 { color: #7f1d1d; background-color: #fecaca; padding: 4px 12px; border-radius: 12px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown('<div class="main-header">👁️ Eyeris - Retinal Screening System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated Diabetic Retinopathy (DR) Severity Grading Prototype &nbsp;|&nbsp; EfficientNet-B0</div>',
    unsafe_allow_html=True,
)

# Mandatory Clinical Disclaimer
st.markdown(
    """
    <div class="disclaimer-banner">
        ⚠️ <strong>Disclaimer:</strong> Research prototype only. Not intended for clinical diagnosis, patient management, or standalone medical decision-making.
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar with model metadata and information
with st.sidebar:
    st.header("📋 Model Information")
    st.markdown("**Architecture:** `EfficientNet-B0`")
    st.markdown("**Version:** `1.0.0`")
    st.markdown("**Input Size:** `224 × 224 RGB`")
    st.markdown("**Classes:** `5 ICDR DR Grades`")
    
    st.markdown("---")
    st.markdown("### Severity Scale")
    st.markdown("""
    - **Grade 0:** No DR
    - **Grade 1:** Mild non-proliferative DR
    - **Grade 2:** Moderate non-proliferative DR
    - **Grade 3:** Severe non-proliferative DR
    - **Grade 4:** Proliferative DR
    """)

    st.markdown("---")
    st.markdown("### ⚠️ Confidence Explanation")
    st.info(
        "**Raw Model Confidence:** The direct softmax probability from the final neural network layer for the top predicted grade.\n\n"
        "**Calibrated Confidence:** Post-processed using isotonic/temperature scaling to reflect true empirical accuracy. In this prototype, raw output is reported directly with calibration delegated to explainability modules."
    )

if IMPORT_ERROR:
    st.error(f"Classification module import error: {IMPORT_ERROR}")
    st.stop()

# Layout: Two columns for upload/preview and analysis
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Fundus Image Upload")
    uploaded_file = st.file_uploader(
        "Upload a retinal fundus photograph (PNG, JPG, JPEG):",
        type=["png", "jpg", "jpeg"],
        help="Upload color fundus photograph centered on macula/optic disc.",
    )

    image = None
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.image(
                image,
                caption=f"Uploaded Fundus Image: {uploaded_file.name} ({image.size[0]}×{image.size[1]}, {image.format})",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Failed to open image file: {e}")
            image = None
    else:
        st.info("Please upload a retinal fundus image to begin screening.")

with col_right:
    st.subheader("2. AI Screening Assessment")
    
    if uploaded_file is not None and image is not None:
        analyze_button = st.button("🔬 Analyze Image", type="primary", use_container_width=True)
        
        if analyze_button:
            with st.spinner("Executing EfficientNet-B0 inference pipeline..."):
                temp_file = None
                try:
                    # Save image temporarily to invoke predict_grade(image_path)
                    suffix = Path(uploaded_file.name).suffix or ".png"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_file.getvalue())
                        temp_file = Path(tmp.name)

                    # Real inference call
                    result = predict_grade(str(temp_file))
                    
                    st.success("Analysis Complete!")

                    # Extract returned outputs
                    pred_grade = result.get("predicted_grade")
                    grade_name = result.get("grade_name", DR_GRADE_LABELS.get(pred_grade, "Unknown"))
                    raw_conf = result.get("raw_confidence", 0.0)
                    probs = result.get("probabilities", [])
                    model_name = result.get("model_name", "efficientnet_b0")
                    model_ver = result.get("model_version", "1.0.0")

                    # Primary Result Metrics
                    badge_class = f"grade-badge-{pred_grade}" if 0 <= pred_grade <= 4 else ""
                    st.markdown(
                        f"""
                        <div style="background-color: #f1f5f9; padding: 18px; border-radius: 8px; margin-bottom: 20px;">
                            <h3 style="margin-top: 0; color: #0f172a;">Diagnostic Assessment</h3>
                            <p style="font-size: 1.25rem; margin-bottom: 8px;">
                                <strong>Predicted Grade:</strong> Grade {pred_grade} — 
                                <span class="{badge_class}">{grade_name}</span>
                            </p>
                            <p style="font-size: 1.05rem; margin-bottom: 0;">
                                <strong>Raw Model Confidence:</strong> {raw_conf * 100:.2f}%
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Detailed Probability Breakdown Table and Chart
                    st.markdown("#### Class Probability Distribution")
                    chart_data = []
                    for g_idx, p_val in enumerate(probs):
                        chart_data.append({
                            "Grade": f"Grade {g_idx} ({DR_GRADE_LABELS.get(g_idx, '')})",
                            "Grade Index": g_idx,
                            "Probability": float(p_val),
                            "Percentage": f"{p_val * 100:.2f}%",
                        })
                    df_probs = pd.DataFrame(chart_data)

                    # Bar chart using Altair
                    chart = (
                        alt.Chart(df_probs)
                        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                        .encode(
                            x=alt.X("Grade:N", sort=None, title="DR Severity Grade"),
                            y=alt.Y("Probability:Q", title="Probability", scale=alt.Scale(domain=[0, 1])),
                            color=alt.condition(
                                alt.datum["Grade Index"] == pred_grade,
                                alt.value("#2563eb"),  # Highlight predicted class
                                alt.value("#94a3b8"),  # Other classes
                            ),
                            tooltip=["Grade", "Percentage"],
                        )
                        .properties(height=260)
                    )
                    st.altair_chart(chart, use_container_width=True)

                    # Probability Table
                    st.dataframe(
                        df_probs[["Grade", "Percentage"]],
                        use_container_width=True,
                        hide_index=True,
                    )

                    # Metadata and Confidence Disclaimer Box
                    st.markdown("---")
                    st.markdown("##### Inference Metadata & Confidence Distinction")
                    st.markdown(
                        f"""
                        - **Model ID:** `{model_name}` (v`{model_ver}`)
                        - **Confidence Type:** **Raw Softmax Confidence** (`{raw_conf * 100:.2f}%`).  
                          *Note: Raw confidence reflects neural network activation and may be uncalibrated or overconfident. It is distinct from post-processed calibrated clinical confidence.*
                        """
                    )

                except Exception as ex:
                    st.error(f"Inference execution failed: {ex}")
                finally:
                    # Clean up temporary file
                    if temp_file and temp_file.exists():
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass
    else:
        st.markdown(
            """
            <div style="border: 2px dashed #cbd5e1; border-radius: 8px; padding: 40px; text-align: center; color: #64748b;">
                Upload a fundus image on the left to activate AI screening analysis.
            </div>
            """,
            unsafe_allow_html=True,
        )
