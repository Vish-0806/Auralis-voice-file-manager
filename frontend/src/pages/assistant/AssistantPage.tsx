import React from 'react';

export const AssistantPage: React.FC = () => {
  return (
    <div>
      <div className="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 className="h2 text-secondary">Voice Assistant</h1>
      </div>
      <div className="card border-0 shadow-sm p-4 text-center">
        <div className="mb-3 text-primary">
          <i className="bi bi-chat-left-dots fs-1"></i>
        </div>
        <h5 className="text-secondary">Assistant Hub</h5>
        <p className="text-muted">
          The Auralis conversational assistant UI will be implemented here in subsequent phases.
        </p>
      </div>
    </div>
  );
};
