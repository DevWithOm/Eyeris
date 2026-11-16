import React from "react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="page-container not-found-page text-center">
      <div className="not-found-card">
        <h1 className="not-found-code">404</h1>
        <h2>Page Not Found</h2>
        <p className="text-secondary mt-2">
          The requested screening view or route does not exist in the EYERIS application.
        </p>
        <div className="mt-4">
          <Link to="/" className="btn btn-primary">
            Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

