import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';
import { Button } from '../../components/common/Button';

export const FilesPage: React.FC = () => {
  const { setDescription, setActions } = useLayout();

  useEffect(() => {
    setDescription('Browse, manage, and search voice file directories.');
    setActions(<Button variant="primary" size="sm" icon="bi-upload">Upload File</Button>);
  }, [setDescription, setActions]);

  return (
    <div className="card border-0 shadow-sm p-4 text-center">
      <div className="mb-3 text-primary">
        <i className="bi bi-folder2-open fs-1"></i>
      </div>
      <h5 className="text-secondary">File Browser</h5>
      <p className="text-muted">
        The voice file manager search controls and document directory browser will be implemented here.
      </p>
    </div>
  );
};
