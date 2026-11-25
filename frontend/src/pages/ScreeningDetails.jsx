import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getExplanation, getScreening } from "../services/api";

export default function ScreeningDetails() {
  const { caseId } = useParams();
  const [screening, setScreening] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchCaseData() {
      try {
        setLoading(true);
        setError(null);
        const [scData, explData] = await Promise.all([
          getScreening(caseId),
          getExplanation(caseId).catch(() => null), // Gracefully handle if explanation endpoint fails
        ]);
        setScreening(scData);
        setExplanation(explData);
      } catch (err) {
        setError(err.message || `Failed to retrieve case details for ${caseId}`);
      } finally {
        setLoading(false);
      }
    }
    fetchCaseData();
  }, [caseId]);

  if (loading) {
    return (
      <div className="page-container loading-container">
        <span className="spinner"></span>
        <p>Loading screening case {caseId}...</p>
      </div>
    );
  }

  if (error || !screening) {
    return (
      <div className="page-container">
        <div className="error-box">
          <h2>Case Not Found or Inaccessible</h2>
          <p>{error || `Case ${caseId} does not exist in the database.`}</p>
          <div className="mt-3">
            <Link to="/history" className="btn btn-primary">Return to History</Link>
          </div>
        </div>
      </div>
    );
  }

  const isGradable = screening.quality_gradable ?? (screening.overall_quality_score >= 0.6);
  const isReferral = Boolean(screening.referable);

  return (
    <div className="page-container screening-details-page">
      {/* Top Breadcrumb & Actions */}
      <div className="details-header">
        <div>
          <div className="breadcrumb">
            <Link to="/history">Screenings</Link> / <span>{screening.case_id}</span>
          </div>
          <h1 className="page-title">
            Case Details: <code className="case-id">{screening.case_id}</code>
          </h1>
          <p className="page-subtitle">
            Examined on {new Date(screening.created_at).toLocaleString()} • Status: <span className="badge badge-info">{screening.status}</span>
          </p>
        </div>

        <div className="header-actions">
          <Link to={`/reports/${screening.case_id}`} className="btn btn-primary">
            📄 View Full Report
          </Link>
          <Link to="/screening/new" className="btn btn-outline">
            + New Screening
          </Link>
        </div>
      </div>

      {/* Primary Triage Alert Banner */}
      <div className={`triage-banner ${isReferral ? "triage-referral" : "triage-routine"}`}>
        <div className="triage-icon">{isReferral ? "⚠️" : "✅"}</div>
        <div className="triage-text">
          <h3>
            {isReferral ? "CLINICAL REFERRAL RECOMMENDED" : "ROUTINE ANNUAL MONITORING RECOMMENDED"}
          </h3>
          <p>
            <strong>Urgency Tier:</strong> {screening.urgency ? screening.urgency.replace("_", " ").toUpperCase() : "ROUTINE"}
          </p>
          <p className="triage-rationale">{screening.rationale || "Automated assessment complete."}</p>
        </div>
      </div>

      {/* Grid of Clinical Cards */}
      <div className="details-grid">
        {/* Quality Assessment Card */}
        <div className="card detail-card">
          <div className="card-header">
            <h3>Image Quality Assessment</h3>
            <span className={`badge ${isGradable ? "badge-success" : "badge-danger"}`}>
              {isGradable ? "GRADABLE" : "UNGRADABLE"}
            </span>
          </div>
          <div className="card-body">
            <div className="metric-row">
              <span className="metric-label">Overall Quality Score:</span>
              <span className="metric-value">
                {screening.overall_quality_score != null
                  ? `${(screening.overall_quality_score * 100).toFixed(1)}%`
                  : "N/A"}
              </span>
            </div>
            {!isGradable && (
              <div className="quality-alert-box mt-2">
                <strong>Attention:</strong> Image quality was flagged as ungradable. Standard imaging protocol advises immediate recapture.
              </div>
            )}
          </div>
        </div>

        {/* DR Classification Card */}
        <div className="card detail-card">
          <div className="card-header">
            <h3>Diabetic Retinopathy Grade</h3>
            {screening.predicted_grade != null ? (
              <span className={`grade-tag grade-${screening.predicted_grade}`}>
                Grade {screening.predicted_grade}
              </span>
            ) : (
              <span className="badge badge-warning">Unavailable</span>
            )}
          </div>
          <div className="card-body">
            {screening.predicted_grade != null ? (
              <>
                <div className="metric-row">
                  <span className="metric-label">Severity Diagnosis:</span>
                  <span className="metric-value">
                    <strong>{screening.grade_name || `Grade ${screening.predicted_grade}`}</strong>
                  </span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Model Engine:</span>
                  <span className="metric-value font-mono">{screening.model_version || "EfficientNet-B0"}</span>
                </div>
              </>
            ) : (
              <div className="unavailable-notice">
                <p><strong>Deep Learning Classification Model Unavailable:</strong></p>
                <p className="subtext">
                  The automated classifier is not loaded or weights are absent. Case has been routed for manual clinical evaluation.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Confidence & Explainability Card */}
        <div className="card detail-card">
          <div className="card-header">
            <h3>Calibrated Confidence & Uncertainty</h3>
          </div>
          <div className="card-body">
            {screening.calibrated_confidence != null ? (
              <>
                <div className="metric-row">
                  <span className="metric-label">Temperature-Calibrated Confidence:</span>
                  <span className="metric-value">{(screening.calibrated_confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="metric-row">
                  <span className="metric-label">Epistemic Uncertainty Score:</span>
                  <span className="metric-value">
                    {screening.uncertainty_score != null ? (screening.uncertainty_score * 100).toFixed(1) + "%" : "N/A"}
                  </span>
                </div>
              </>
            ) : (
              <div className="unavailable-notice">
                <p>Confidence calibration metrics not computed for this record.</p>
              </div>
            )}

            {explanation && explanation.gradcam_heatmap_url && (
              <div className="mt-2">
                <span className="badge badge-info">Grad-CAM Heatmap Generated</span>
              </div>
            )}
          </div>
        </div>

        {/* Action Required Card */}
        <div className="card detail-card">
          <div className="card-header">
            <h3>Clinical Next Steps</h3>
          </div>
          <div className="card-body">
            <p className="action-text">{screening.action_required || "Standard protocol follow-up."}</p>
            <div className="mt-3">
              <Link to={`/reports/${screening.case_id}`} className="btn btn-secondary btn-block">
                Generate Official Handoff Report
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

