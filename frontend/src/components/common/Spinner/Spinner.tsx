import React from 'react';

export interface SpinnerProps {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'light' | 'dark';
  size?: 'sm' | 'md' | 'lg';
  type?: 'border' | 'grow';
  srText?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  variant = 'primary',
  size = 'md',
  type = 'border',
  srText = 'Loading...',
  className = ''
}) => {
  const spinnerClass = `spinner-${type}`;
  const colorClass = `text-${variant}`;
  const sizeClass = size === 'sm' ? `${spinnerClass}-sm` : size === 'lg' ? 'spinner-lg' : '';

  const classes = [spinnerClass, colorClass, sizeClass, className].filter(Boolean).join(' ');

  const inlineStyle: React.CSSProperties | undefined =
    size === 'lg'
      ? { width: '3rem', height: '3rem' }
      : undefined;

  return (
    <div className={classes} role="status" style={inlineStyle}>
      <span className="visually-hidden">{srText}</span>
    </div>
  );
};
