import React, { useId } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, helperText, error, className = '', id, required, ...props }, ref) => {
    const defaultId = useId();
    const inputId = id || defaultId;
    const helperId = `${inputId}-helper`;
    const errorId = `${inputId}-error`;

    const hasHelper = !!helperText;
    const hasError = !!error;

    const describedBy = [
      hasHelper ? helperId : '',
      hasError ? errorId : ''
    ].filter(Boolean).join(' ') || undefined;

    return (
      <div className="mb-3">
        {label && (
          <label htmlFor={inputId} className="form-label fw-medium">
            {label}
            {required && <span className="text-danger ms-1" aria-hidden="true">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          required={required}
          aria-invalid={hasError ? 'true' : undefined}
          aria-describedby={describedBy}
          className={`form-control ${error ? 'is-invalid' : ''} ${className}`.trim()}
          {...props}
        />
        {hasError && (
          <div id={errorId} className="invalid-feedback" aria-live="assertive">
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

Input.displayName = 'Input';
