import React from 'react';

export interface ProgressProps {
  value: number;
  min?: number;
  max?: number;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'dark';
  striped?: boolean;
  animated?: boolean;
  showLabel?: boolean;
  className?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  min = 0,
  max = 100,
  variant = 'primary',
  striped = false,
  animated = false,
  showLabel = false,
  className = ''
}) => {
  const percentage = Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100);

  const barClasses = [
    'progress-bar',
    `bg-${variant}`,
    striped ? 'progress-bar-striped' : '',
    animated ? 'progress-bar-animated' : ''
  ].filter(Boolean).join(' ');

  return (
    <div className={`progress ${className}`.trim()} style={{ height: '1.25rem' }}>
      <div
        className={barClasses}
        role="progressbar"
        style={{ width: `${percentage}%` }}
        aria-valuenow={value}
        aria-valuemin={min}
        aria-valuemax={max}
      >
        {showLabel && `${Math.round(percentage)}%`}
      </div>
    </div>
  );
};
