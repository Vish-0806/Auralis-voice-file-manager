import React from 'react';

export interface ToastProps {
  title: string;
  message: string;
  metaText?: string;
  icon?: string;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'dark';
  onClose?: () => void;
  className?: string;
}

export const Toast: React.FC<ToastProps> = ({
  title,
  message,
  metaText,
  icon,
  variant = 'primary',
  onClose,
  className = ''
}) => {
  return (
    <div
      className={`toast show border-${variant} ${className}`.trim()}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="toast-header">
        {icon && <i className={`bi ${icon} text-${variant} me-2`} />}
        <strong className="me-auto">{title}</strong>
        {metaText && <small className="text-muted">{metaText}</small>}
        {onClose && (
          <button
            type="button"
            className="btn-close"
            aria-label="Close"
            onClick={onClose}
          />
        )}
      </div>
      <div className="toast-body">{message}</div>
    </div>
  );
};
