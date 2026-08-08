import React from 'react';

interface WorkspaceLayoutProps {
  children: React.ReactNode;
}

export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({ children }) => {
  return (
    <div className="container-fluid py-2">
      <div className="row">
        <div className="col-12">
          {children}
        </div>
      </div>
    </div>
  );
};
