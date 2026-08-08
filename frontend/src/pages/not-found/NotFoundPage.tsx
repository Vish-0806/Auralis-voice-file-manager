import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center text-center p-5" style={{ minHeight: '60vh' }}>
      <div className="text-danger mb-3">
        <i className="bi bi-exclamation-triangle fs-1"></i>
      </div>
      <h1 className="display-4 fw-bold text-secondary">404</h1>
      <h3 className="h5 text-muted mb-4">Page Not Found</h3>
      <p className="text-muted mb-4 max-w-md">
        The screen or location you requested does not exist. Check the URL or click below to return home.
      </p>
      <Link to="/" className="btn btn-primary d-inline-flex align-items-center">
        <i className="bi bi-house-door me-2"></i>
        Back to Dashboard
      </Link>
    </div>
  );
};
