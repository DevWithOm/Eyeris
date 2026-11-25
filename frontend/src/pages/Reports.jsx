import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../services/api";

export default function Reports() {
  const { caseId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadReport() {
      try {
        setLoading(true);
        setError(null);
        const data = await getReport(caseId);
        setReport(data);
      } catch (err) {
        setError(err.message || `Failed to generate screening report for case ${caseId}`);
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, [caseId]);

  if (loading) {
    return (
      <div className="page-container loading-container">
        <span className="spinner"></span>
        <p>Compiling clinical report for case {caseId}...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="page-container">
        <div className="error-box">
          <h2>Report Generation Error</h2>
          <p>{error || "Unable to compile report."}</p>
          <div className="mt-3">
            <Link to="/history" className="btn btn-primary">Return to History</Link>
          </div>
        </div>
      </div>
    );
  }

  const result = report.screening_result || {};
  const decision = result.clinical_decision || {};
  const quality = result.quality || {};
  const classification = result.classification || {};

  return (
    <div className="page-container report-page">
      {/* Non-Printable Header & Toolbar */}
      <div className="no-print report-toolbar">
        <div>
          <Link to={`/screening/${caseId}`} className="link-back">← Back to Case Details</Link>
          <h1 className="page-title mt-1">Screening Summary Report</h1>
          <p className="page-subtitle">Standardized clinical summary for patient record integration and referral handoff.</p>
        </div>

        <div className="report-actions">
          <button onClick={() => window.print()} className="btn btn-primary">
            🖨 Print / Export PDF
          </button>
        </div>
      </div>

      {/* Printable Report Document Sheet */}
      <article className="report-sheet">
        <header className="report-sheet-header">
          <div className="report-brand">
            <h2>EYERIS Screening Decision Support</h2>
            <p className="report-subtext">Automated Diabetic Retinopathy Triage System • SIH PS26038</p>
          </div>
          <div className="report-meta">
            <div><strong>Report ID:</strong> {report.report_id}</div>
            <div><strong>Case ID:</strong> <code className="case-id">{report.case_id}</code></div>
            <div><strong>Generated:</strong> {new Date(report.generated_at).toLocaleString()}</div>
          </div>
        </header>

        <hr className="report-divider" />

        {/* Clinical Summary Section */}
        <section className="report-section">
          <h3>1. Clinical Triage Summary</h3>
          <div className="report-grid">
            <div className="report-field">
              <span className="field-label">Referral Recommendation:</span>
              <span className={`field-value font-bold ${decision.referral_recommended ? "text-danger" : "text-success"}`}>
                {decision.referral_recommended ? "REFERRAL TO OPHTHALMOLOGIST RECOMMENDED" : "ROUTINE ANNUAL RESCREENING"}
              </span>
            </div>
            <div className="report-field">
              <span className="field-label">Urgency Timeframe:</span>
              <span className="field-value font-bold">
                {decision.urgency ? decision.urgency.replace("_", " ").toUpperCase() : "ROUTINE"}
              </span>
            </div>
            <div className="report-field">
              <span className="field-label">DR Severity Grade:</span>
              <span className="field-value">
                {classification.grade_name || (classification.predicted_grade != null ? `Grade ${classification.predicted_grade}` : "Model Unavailable — Manual Review")}
              </span>
            </div>
            <div className="report-field">
              <span className="field-label">Overall Quality Assessment:</span>
              <span className="field-value">
                {quality.is_gradable ? "GRADABLE" : "UNGRADABLE"} ({quality.overall_quality_score != null ? `${(quality.overall_quality_score * 100).toFixed(0)}%` : "N/A"})
              </span>
            </div>
          </div>
        </section>

        {/* Clinical Rationale & Action Required */}
        <section className="report-section">
          <h3>2. Decision Rationale & Recommended Actions</h3>
          <div className="callout-box">
            <p><strong>Rationale:</strong> {decision.rationale || "Automated rule evaluation completed."}</p>
            <p className="mt-2"><strong>Recommended Action:</strong> {decision.action_required || "Routine clinical follow-up."}</p>
          </div>
        </section>

        {/* Raw Markdown Output */}
        <section className="report-section markdown-summary-section">
          <h3>3. Complete Screening Manifest</h3>
          <pre className="markdown-pre">{report.summary_markdown}</pre>
        </section>

        {/* Clinical Sign-off & Regulatory Notice */}
        <footer className="report-sheet-footer">
          <div className="signoff-box">
            <p><strong>Reviewing Clinician Sign-Off:</strong></p>
            <div className="signature-line">
              <span>Signature: ___________________________</span>
              <span>Date: _______________</span>
            </div>
          </div>

          <p className="report-disclaimer">
            <strong>IMPORTANT REGULATORY NOTICE:</strong> This document was generated by the EYERIS research screening prototype (SIH PS26038). It does not represent an automated clinical diagnosis. Confirmation by a certified optometrist or ophthalmologist is mandatory prior to medical intervention.
          </p>
        </footer>
      </article>
    </div>
  );
}

