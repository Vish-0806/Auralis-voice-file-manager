import React from 'react';

export const FilesPage: React.FC = () => {
  return (
    <div>
      <div className="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 className="h2 text-secondary">File Manager</h1>
      </div>
      <div className="card border-0 shadow-sm p-4 text-center">
        <div className="mb-3 text-primary">
          <i className="bi bi-folder2-open fs-1"></i>
        </div>
        <h5 className="text-secondary">File Browser</h5>
        <p className="text-muted">
          The voice file manager search controls and document directory browser will be implemented here.
        </p>
      </div>
    </div>
  );
};
