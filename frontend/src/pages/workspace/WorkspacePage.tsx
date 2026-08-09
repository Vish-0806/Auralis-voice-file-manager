import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';
import { WorkspaceShell } from '../../features/workspace';

export const WorkspacePage: React.FC = () => {
  const { setDescription } = useLayout();

  useEffect(() => {
    setDescription('Active file buffers and document staging operations.');
  }, [setDescription]);

  return (
    <div className="container-fluid px-0">
      <WorkspaceShell />
    </div>
  );
};
export default WorkspacePage;
