import React from 'react';
import { WorkspaceLayout } from '../../layouts/WorkspaceLayout';

export const WorkspacePage: React.FC = () => {
  return (
    <WorkspaceLayout>
      <div className="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 className="h2 text-secondary">Workspace</h1>
      </div>
      <div className="card border-0 shadow-sm p-4 text-center">
        <div className="mb-3 text-primary">
          <i className="bi bi-kanban fs-1"></i>
        </div>
        <h5 className="text-secondary">Workspace Operations</h5>
        <p className="text-muted">
          Active files workspace and editing buffers will be rendered here.
        </p>
      </div>
    </WorkspaceLayout>
  );
};
