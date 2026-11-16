import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listScreenings } from "../services/api";

export default function ScreeningHistory() {
  const [screenings, setScreenings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterReferableOnly, setFilterReferableOnly] = useState(false);

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true);
        const data = await listScreenings(100, 0);
        setScreenings(data || []);
      } catch (err) {
        setError(err.message || "Failed to load screening history.");
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  const filteredScreenings = screenings.filter((sc) => {
    const matchesSearch =
      sc.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (sc.grade_name && sc.grade_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (sc.status && sc.status.toLowerCase().includes(searchTerm.toLowerCase()));

    if (filterReferableOnly) {
      return matchesSearch && sc.referable;
    }
    return matchesSearch;
  });

  return (
    <div className="page-container history-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Screening Case Records</h1>
          <p className="page-subtitle">Historical log of all processed diabetic retinopathy screening examinations.</p>
        </div>
        <Link to="/screening/new" className="btn btn-primary">
          + New Screening
        </Link>
      </div>

      {/* Filter Toolbar */}
      <div className="filter-toolbar">
        <div className="search-box">
          <input
            type="text"
            className="form-control"
            placeholder="Search by Case ID, Grade, or Status..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-checkbox">
          <label>
            <input
              type="checkbox"
              checked={filterReferableOnly}
              onChange={(e) => setFilterReferableOnly(e.target.checked)}
            />
            Show Referrals Only
          </label>
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <div className="loading-state">
          <span className="spinner"></span>
          <p>Retrieving screening records from database...</p>
        </div>
      ) : error ? (
        <div className="error-box">
          <h3>Error Loading Records</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="btn btn-outline mt-2">
            Retry Connection
          </button>
        </div>
      ) : filteredScreenings.length === 0 ? (
        <div className="empty-state">
          <p className="empty-title">No matching records found</p>
          <p className="empty-text">
            {searchTerm || filterReferableOnly
              ? "No screening records match your active search filters."
              : "No screenings have been recorded yet."}
          </p>
          <Link to="/screening/new" className="btn btn-primary mt-3">
            Submit First Screening
          </Link>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Timestamp</th>
                <th>Quality Assessment</th>
                <th>DR Severity Grade</th>
                <th>Triage Decision</th>
                <th>Urgency Timeframe</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredScreenings.map((sc) => (
                <tr key={sc.case_id}>
                  <td>
                    <code className="case-id">{sc.case_id}</code>
                  </td>
                  <td>{new Date(sc.created_at).toLocaleString()}</td>
                  <td>
                    {sc.overall_quality_score != null ? (
                      <span className={`badge ${sc.overall_quality_score >= 0.6 ? "badge-success" : "badge-danger"}`}>
                        {(sc.overall_quality_score * 100).toFixed(0)}% ({sc.quality_gradable ? "Gradable" : "Ungradable"})
                      </span>
                    ) : (
                      "N/A"
                    )}
                  </td>
                  <td>
                    {sc.grade_name ? (
                      <span className={`grade-tag grade-${sc.predicted_grade}`}>
                        {sc.grade_name} (Grade {sc.predicted_grade})
                      </span>
                    ) : (
                      <span className="text-muted">Classification Unavailable</span>
                    )}
                  </td>
                  <td>
                    {sc.referable ? (
                      <span className="badge badge-referral">REFERRAL</span>
                    ) : (
                      <span className="badge badge-normal">ROUTINE</span>
                    )}
                  </td>
                  <td>
                    <span className="urgency-label">{sc.urgency ? sc.urgency.replace("_", " ") : "routine"}</span>
                  </td>
                  <td>
                    <div className="action-buttons">
                      <Link to={`/screening/${sc.case_id}`} className="btn btn-sm btn-outline">
                        Inspect
                      </Link>
                      <Link to={`/reports/${sc.case_id}`} className="btn btn-sm btn-secondary">
                        Report
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

