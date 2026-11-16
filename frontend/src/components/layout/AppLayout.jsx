import React from "react";
import Navbar from "./Navbar";
import DisclaimerBanner from "./DisclaimerBanner";

export default function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <Navbar />
      <DisclaimerBanner />
      <main className="main-content" id="main-content">
        {children}
      </main>
      <footer className="footer">
        <div className="footer-content">
          <p>© 2026 EYERIS Team. SIH Problem Statement PS26038. All rights reserved.</p>
          <p className="footer-subtext">Designed for research triage, rural outreach, and clinical decision support.</p>
        </div>
      </footer>
    </div>
  );
}

