import React from 'react';

export interface ErrorStateProps {
  title: string;
  description: string;
  icon?: string;
  onRetry?: () => void;
  retryText?: string;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  description,
  icon = 'bi-exclamation-triangle',
  onRetry,
  retryText = 'Retry',
  className = ''
}) => {
  return (
    <div
      className={`d-flex flex-column align-items-center justify-content-center text-center p-5 rounded border border-danger-subtle bg-danger-subtle bg-opacity-10 ${className}`.trim()}
    >
      <div className="mb-3 text-danger" style={{ fontSize: '3rem' }}>
        <i className={`bi ${icon}`} />
      </div>
      <h3 className="h4 fw-semibold text-danger-emphasis mb-2">{title}</h3>
      <p className="text-muted mb-4" style={{ maxWidth: '400px' }}>{description}</p>
      {onRetry && (
        <button type="button" className="btn btn-outline-danger btn-sm" onClick={onRetry}>
          {retryText}
        </button>
      )}
    </div>
  );
};
