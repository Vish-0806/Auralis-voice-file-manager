import React from 'react';
import { DashboardLayout } from '../../layouts/DashboardLayout';

export const DashboardPage: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 className="h2 text-secondary">Dashboard</h1>
      </div>

      <div className="row g-4 mb-4">
        {/* Card 1 */}
        <div className="col-12 col-md-6 col-lg-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0 bg-primary text-white p-3 rounded-3">
                  <i className="bi bi-folder-fill fs-4"></i>
                </div>
                <div className="flex-grow-1 ms-3">
                  <h6 className="card-subtitle mb-1 text-muted text-uppercase small">Total Files</h6>
                  <h5 className="card-title mb-0 fw-bold">0</h5>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Card 2 */}
        <div className="col-12 col-md-6 col-lg-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0 bg-success text-white p-3 rounded-3">
                  <i className="bi bi-mic-fill fs-4"></i>
                </div>
                <div className="flex-grow-1 ms-3">
                  <h6 className="card-subtitle mb-1 text-muted text-uppercase small">Voice Commands</h6>
                  <h5 className="card-title mb-0 fw-bold">0</h5>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Card 3 */}
        <div className="col-12 col-md-6 col-lg-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0 bg-warning text-white p-3 rounded-3">
                  <i className="bi bi-activity fs-4"></i>
                </div>
                <div className="flex-grow-1 ms-3">
                  <h6 className="card-subtitle mb-1 text-muted text-uppercase small">Active Tasks</h6>
                  <h5 className="card-title mb-0 fw-bold">0</h5>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Card 4 */}
        <div className="col-12 col-md-6 col-lg-3">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0 bg-info text-white p-3 rounded-3">
                  <i className="bi bi-cpu-fill fs-4"></i>
                </div>
                <div className="flex-grow-1 ms-3">
                  <h6 className="card-subtitle mb-1 text-muted text-uppercase small">System Status</h6>
                  <h5 className="card-title mb-0 fw-bold">Online</h5>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card border-0 shadow-sm p-4">
        <h4 className="h5 text-muted mb-3">Welcome to Auralis V2</h4>
        <p className="text-secondary mb-0">
          This is a clean-slate rebuild of the frontend application architecture. All old runtime layers 
          have been removed, laying down a simple and maintainable foundation for future phases.
        </p>
      </div>
    </DashboardLayout>
  );
};
