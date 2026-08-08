import React from 'react';

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'rect' | 'circle';
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1rem',
  variant = 'text',
  className = ''
}) => {
  const getBorderRadius = () => {
    if (variant === 'circle') return '50%';
    if (variant === 'rect') return '4px';
    return '0.25rem';
  };

  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
    borderRadius: getBorderRadius(),
    backgroundColor: 'var(--bs-secondary-bg, #e9ecef)',
    display: 'inline-block'
  };

  return (
    <div
      className={`placeholder-glow w-100 ${className}`.trim()}
      aria-hidden="true"
    >
      <span
        className="placeholder w-100"
        style={style}
      />
    </div>
  );
};
