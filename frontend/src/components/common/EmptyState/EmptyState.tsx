import React from 'react';

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon = 'bi-folder-x',
  action,
  className = ''
}) => {
  return (
    <div
      className={`d-flex flex-column align-items-center justify-content-center text-center p-5 rounded border border-dashed bg-light-subtle ${className}`.trim()}
    >
      <div className="mb-3 text-secondary" style={{ fontSize: '3rem' }}>
        <i className={`bi ${icon}`} />
      </div>
      <h3 className="h4 fw-semibold text-body-emphasis mb-2">{title}</h3>
      <p className="text-muted mb-4" style={{ maxWidth: '400px' }}>{description}</p>
      {action && <div className="d-flex justify-content-center">{action}</div>}
    </div>
  );
};
