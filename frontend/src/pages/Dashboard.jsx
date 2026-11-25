import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listScreenings } from "../services/api";

export default function Dashboard() {
  const [screenings, setScreenings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await listScreenings(5, 0);
        setScreenings(data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalCount = screenings.length;
  const referableCount = screenings.filter((s) => s.referable).length;
  const ungradableCount = screenings.filter((s) => s.status === "rejected_quality").length;

  return (
    <div className="page-container dashboard-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Screening Operations Dashboard</h1>
          <p className="page-subtitle">Diabetic Retinopathy automated triage and decision-support workspace.</p>
        </div>
        <Link to="/screening/new" className="btn btn-primary">
          + Start New Screening
        </Link>
      </div>

      {/* KPI Stats Grid */}
      <section className="stats-grid" aria-label="Screening statistics">
        <div className="stat-card">
          <div className="stat-label">Recent Cases Checked</div>
          <div className="stat-value">{totalCount}</div>
          <div className="stat-hint">Active session window</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Referrals Recommended</div>
          <div className="stat-value text-danger">{referableCount}</div>
          <div className="stat-hint">Potentially referable (Grades 2–4 or uncertain)</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Quality Rejections</div>
          <div className="stat-value text-warning">{ungradableCount}</div>
          <div className="stat-hint">Recapture required due to blur/illumination</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">AI Pipeline State</div>
          <div className="stat-value text-accent">Active (v1.0)</div>
          <div className="stat-hint">FastAPI orchestrator ready</div>
        </div>
      </section>

      {/* Workflow Navigation Cards */}
      <section className="action-grid" aria-label="Workflow shortcuts">
        <div className="action-card">
          <h3>Retinal Fundus Intake</h3>
          <p>Upload patient fundus photographs (JPEG/PNG) for automated image quality assessment and DR triage.</p>
          <Link to="/screening/new" className="btn btn-secondary">
            Upload & Analyze Case →
          </Link>
        </div>
        <div className="action-card">
          <h3>Screening History & Records</h3>
          <p>Inspect past patient cases, filter by referral status, and review historical screening decisions.</p>
          <Link to="/history" className="btn btn-secondary">
            Browse All Records →
          </Link>
        </div>
      </section>

      {/* Recent Screenings Section */}
      <section className="recent-screenings-section">
        <div className="section-header">
          <h2>Recent Screenings</h2>
          <Link to="/history" className="link-more">View all →</Link>
        </div>

        {loading ? (
          <div className="loading-state">
            <span className="spinner"></span>
            <p>Loading recent screenings...</p>
          </div>
        ) : error ? (
          <div className="error-box">
            <p><strong>Note:</strong> {error}</p>
          </div>
        ) : screenings.length === 0 ? (
          <div className="empty-state">
            <p className="empty-title">No screenings found</p>
            <p className="empty-text">No retinal fundus images have been screened yet in this session.</p>
            <Link to="/screening/new" className="btn btn-primary mt-3">
              Screen First Patient
            </Link>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Date & Time</th>
                  <th>Status</th>
                  <th>Quality</th>
                  <th>DR Grade</th>
                  <th>Referral</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {screenings.map((sc) => (
                  <tr key={sc.case_id}>
                    <td>
                      <code className="case-id">{sc.case_id}</code>
                    </td>
                    <td>{new Date(sc.created_at).toLocaleString()}</td>
                    <td>
                      <span className={`badge badge-${sc.status}`}>{sc.status}</span>
                    </td>
                    <td>
                      {sc.overall_quality_score != null ? `${(sc.overall_quality_score * 100).toFixed(0)}%` : "N/A"}
                    </td>
                    <td>
                      {sc.grade_name || (sc.predicted_grade != null ? `Grade ${sc.predicted_grade}` : "Unavailable")}
                    </td>
                    <td>
                      {sc.referable ? (
                        <span className="badge badge-referral">REFERRAL</span>
                      ) : (
                        <span className="badge badge-normal">Routine</span>
                      )}
                    </td>
                    <td>
                      <Link to={`/screening/${sc.case_id}`} className="btn btn-sm btn-outline">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

