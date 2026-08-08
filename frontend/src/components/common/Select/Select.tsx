import React, { useId } from 'react';

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  helperText?: string;
  error?: string;
  options?: SelectOption[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, helperText, error, options, className = '', id, required, children, ...props }, ref) => {
    const defaultId = useId();
    const selectId = id || defaultId;
    const helperId = `${selectId}-helper`;
    const errorId = `${selectId}-error`;

    const hasHelper = !!helperText;
    const hasError = !!error;

    const describedBy = [
      hasHelper ? helperId : '',
      hasError ? errorId : ''
    ].filter(Boolean).join(' ') || undefined;

    return (
      <div className="mb-3">
        {label && (
          <label htmlFor={selectId} className="form-label fw-medium">
            {label}
            {required && <span className="text-danger ms-1" aria-hidden="true">*</span>}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          required={required}
          aria-invalid={hasError ? 'true' : undefined}
          aria-describedby={describedBy}
          className={`form-select ${error ? 'is-invalid' : ''} ${className}`.trim()}
          {...props}
        >
          {options
            ? options.map((opt) => (
                <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                  {opt.label}
                </option>
              ))
            : children}
        </select>
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

Select.displayName = 'Select';
