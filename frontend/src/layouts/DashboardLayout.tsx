import React from 'react';
import { Outlet } from 'react-router-dom';

interface DashboardLayoutProps {
  children?: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
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
