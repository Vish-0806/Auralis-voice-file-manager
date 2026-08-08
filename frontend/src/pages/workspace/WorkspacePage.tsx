import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';
import { Button } from '../../components/common/Button';

export const WorkspacePage: React.FC = () => {
  const { setDescription, setActions } = useLayout();

  useEffect(() => {
    setDescription('Active file buffers and document staging operations.');
    setActions(<Button variant="success" size="sm" icon="bi-save">Save Buffer</Button>);
  }, [setDescription, setActions]);

  return (
    <div className="card border-0 shadow-sm p-4 text-center">
      <div className="mb-3 text-primary">
        <i className="bi bi-kanban fs-1"></i>
      </div>
      <h5 className="text-secondary">Workspace Operations</h5>
      <p className="text-muted">
        Active files workspace and editing buffers will be rendered here.
      </p>
    </div>
  );
};
