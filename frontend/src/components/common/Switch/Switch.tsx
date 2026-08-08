import React, { useId } from 'react';

export interface SwitchProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ label, error, helperText, className = '', id, ...props }, ref) => {
    const defaultId = useId();
    const switchId = id || defaultId;
    const errorId = `${switchId}-error`;
    const helperId = `${switchId}-helper`;

    const hasError = !!error;
    const hasHelper = !!helperText;

    const describedBy = [
      hasHelper ? helperId : '',
      hasError ? errorId : ''
    ].filter(Boolean).join(' ') || undefined;

    return (
      <div className="form-check form-switch mb-3">
        <input
          ref={ref}
          type="checkbox"
          role="switch"
          id={switchId}
          aria-invalid={hasError ? 'true' : undefined}
          aria-describedby={describedBy}
          className={`form-check-input ${error ? 'is-invalid' : ''} ${className}`.trim()}
          {...props}
        />
        {label && (
          <label htmlFor={switchId} className="form-check-label fw-medium select-none">
            {label}
          </label>
        )}
        {hasError && (
          <div id={errorId} className="invalid-feedback d-block" aria-live="assertive">
            {error}
          </div>
        )}
        {hasHelper && !hasError && (
          <div id={helperId} className="form-text text-muted">
            {helperText}
          </div>
        )}
      </div>
    );
  }
);

Switch.displayName = 'Switch';
