import React, { useId } from 'react';

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, error, helperText, className = '', id, ...props }, ref) => {
    const defaultId = useId();
    const checkboxId = id || defaultId;
    const errorId = `${checkboxId}-error`;
    const helperId = `${checkboxId}-helper`;

    const hasError = !!error;
    const hasHelper = !!helperText;

    const describedBy = [
      hasHelper ? helperId : '',
      hasError ? errorId : ''
    ].filter(Boolean).join(' ') || undefined;

    return (
      <div className="form-check mb-3">
        <input
          ref={ref}
          type="checkbox"
          id={checkboxId}
          aria-invalid={hasError ? 'true' : undefined}
          aria-describedby={describedBy}
          className={`form-check-input ${error ? 'is-invalid' : ''} ${className}`.trim()}
          {...props}
        />
        {label && (
          <label htmlFor={checkboxId} className="form-check-label fw-medium select-none">
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

Checkbox.displayName = 'Checkbox';
