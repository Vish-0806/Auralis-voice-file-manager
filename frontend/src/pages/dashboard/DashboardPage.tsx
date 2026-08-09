import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';
import {
  DashboardHeader,
  SystemStatus,
  QuickActions,
  RecentFiles,
  WorkspaceSummary,
  RecentActivity
} from '../../features/dashboard';

export const DashboardPage: React.FC = () => {
  const { setDescription } = useLayout();

  useEffect(() => {
    setDescription('Overview of system status, tasks, and voice file manager metrics.');
  }, [setDescription]);

  return (
    <div className="container-fluid px-0">
      <DashboardHeader />
      
      <div className="row g-4 mb-4">
        <div className="col-12 col-lg-8">
          <QuickActions />
        </div>
        <div className="col-12 col-lg-4">
          <SystemStatus />
        </div>
      </div>

      <div className="row g-4">
        <div className="col-12 col-md-6 col-lg-4">
          <RecentFiles />
        </div>
        <div className="col-12 col-md-6 col-lg-4">
          <WorkspaceSummary />
        </div>
        <div className="col-12 col-lg-4">
          <RecentActivity />
        </div>
      </div>
    </div>
  );
};
export default DashboardPage;
