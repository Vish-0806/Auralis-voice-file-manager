import React from 'react';
import { Outlet } from 'react-router-dom';

interface WorkspaceLayoutProps {
  children?: React.ReactNode;
}

export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({ children }) => {
  return (
    <div className="container-fluid py-2">
      <div className="row">
        <div className="col-12">
          {children || <Outlet />}
        </div>
      </div>
    </div>
  );
};
