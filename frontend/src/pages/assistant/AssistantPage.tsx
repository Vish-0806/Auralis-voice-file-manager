import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';

export const AssistantPage: React.FC = () => {
  const { setDescription } = useLayout();

  useEffect(() => {
    setDescription('Interactive natural language conversational hub.');
  }, [setDescription]);

  return (
    <div className="card border-0 shadow-sm p-4 text-center">
      <div className="mb-3 text-primary">
        <i className="bi bi-chat-left-dots fs-1"></i>
      </div>
      <h5 className="text-secondary">Assistant Hub</h5>
      <p className="text-muted">
        The Auralis conversational assistant UI will be implemented here in subsequent phases.
      </p>
    </div>
  );
};
