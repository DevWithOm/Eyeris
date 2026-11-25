import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { checkHealth } from "../../services/api";

export default function Navbar() {
  const location = useLocation();
  const [backendStatus, setBackendStatus] = useState({ checked: false, connected: false });

  useEffect(() => {
    let isMounted = true;
    async function verifyBackend() {
      try {
        const res = await checkHealth();
        if (isMounted) {
          setBackendStatus({ checked: true, connected: res.status === "ok" || res.status === "degraded" });
        }
      } catch {
        if (isMounted) {
          setBackendStatus({ checked: true, connected: false });
        }
      }
    }
    verifyBackend();
    const interval = setInterval(verifyBackend, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navLinks = [
    { to: "/", label: "Dashboard" },
    { to: "/screening/new", label: "New Screening" },
    { to: "/history", label: "Screening History" },
  ];

  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <Link to="/" className="brand-logo">
            <span className="brand-icon">👁</span>
            <span className="brand-title">EYERIS</span>
          </Link>
          <span className="brand-subtitle">DR Screening Support</span>
        </div>

        <nav className="navbar-links">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`nav-link ${location.pathname === link.to ? "active" : ""}`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="navbar-status">
          {backendStatus.checked ? (
            <span
              className={`status-pill ${backendStatus.connected ? "connected" : "disconnected"}`}
              title={backendStatus.connected ? "FastAPI backend reachable" : "Backend unreachable at :8000"}
            >
              <span className="status-dot"></span>
              {backendStatus.connected ? "API Connected" : "API Offline"}
            </span>
          ) : (
            <span className="status-pill checking">
              <span className="status-dot"></span> Checking API...
            </span>
          )}
        </div>
      </div>
    </header>
  );
}

