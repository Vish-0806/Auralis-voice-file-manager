import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';
import { Button } from '../../components/common/Button';

export const SettingsPage: React.FC = () => {
  const { setDescription, setActions } = useLayout();

  useEffect(() => {
    setDescription('Configure interface theme settings and local API base URLs.');
    setActions(<Button variant="primary" size="sm" icon="bi-check-lg">Save Prefs</Button>);
  }, [setDescription, setActions]);

  return (
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
  );
};
