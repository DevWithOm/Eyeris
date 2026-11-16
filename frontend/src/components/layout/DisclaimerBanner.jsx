import React from "react";

export default function DisclaimerBanner() {
  return (
    <aside className="disclaimer-banner" role="complementary" aria-label="Medical research notice">
      <div className="disclaimer-content">
        <span className="disclaimer-icon">⚠️</span>
        <span className="disclaimer-text">
          <strong>Research Screening Prototype:</strong> EYERIS is being developed for SIH Problem Statement PS26038 as an investigational screening decision-support tool. It is <em>not</em> an autonomous diagnostic medical device. All recommendations require confirmation by a qualified clinician.
        </span>
      </div>
    </aside>
  );
}

