import React from 'react';

export const SettingsPage: React.FC = () => {
  return (
    <div>
      <div className="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 className="h2 text-secondary">Settings</h1>
      </div>
      <div className="card border-0 shadow-sm p-4">
        <h5 className="text-secondary mb-3">Application Preferences</h5>
        <form onSubmit={(e) => e.preventDefault()}>
          <div className="mb-3">
            <label className="form-label text-muted small fw-bold">API Base URL</label>
            <input 
              type="text" 
              className="form-control" 
              value={import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'} 
              disabled 
            />
          </div>
          <div className="mb-3">
            <label className="form-label text-muted small fw-bold">Theme Mode</label>
            <select className="form-select" disabled>
              <option>System Default</option>
              <option>Light</option>
              <option>Dark</option>
            </select>
          </div>
        </form>
      </div>
    </div>
  );
};
