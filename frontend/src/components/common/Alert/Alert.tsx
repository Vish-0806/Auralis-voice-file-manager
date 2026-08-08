import React from 'react';

export interface AlertProps {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'light' | 'dark';
  dismissible?: boolean;
  onClose?: () => void;
  className?: string;
  children: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'warning',
  dismissible = false,
  onClose,
  className = '',
  children
}) => {
  const classes = [
    'alert',
    `alert-${variant}`,
    dismissible ? 'alert-dismissible fade show' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} role="alert">
      {children}
      {dismissible && (
        <button
          type="button"
          className="btn-close"
          aria-label="Close"
          onClick={onClose}
        />
      )}
    </div>
  );
};
