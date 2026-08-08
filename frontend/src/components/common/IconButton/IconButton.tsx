import React from 'react';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: string;
  variant?:
    | 'primary'
    | 'secondary'
    | 'success'
    | 'danger'
    | 'warning'
    | 'info'
    | 'light'
    | 'dark'
    | 'outline-primary'
    | 'outline-secondary'
    | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  tooltip?: string;
  'aria-label': string;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  variant = 'ghost',
  size = 'md',
  loading = false,
  tooltip,
  className = '',
  disabled,
  ...props
}) => {
  const btnClass = variant === 'ghost' ? 'btn-link text-decoration-none text-body p-1' : `btn-${variant}`;
  const sizeClass = size !== 'md' ? `btn-${size}` : '';

  const classes = [
    'btn',
    'd-inline-flex',
    'align-items-center',
    'justify-content-center',
    btnClass,
    sizeClass,
    className
  ].filter(Boolean).join(' ');

  const isDisabled = disabled || loading;

  return (
    <button
      className={classes}
      disabled={isDisabled}
      title={tooltip}
      aria-busy={loading ? 'true' : undefined}
      {...props}
    >
      {loading ? (
        <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" />
      ) : (
        <i className={`bi ${icon}`} />
      )}
    </button>
  );
};
