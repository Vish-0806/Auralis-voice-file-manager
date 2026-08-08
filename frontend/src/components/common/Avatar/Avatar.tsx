import React, { useState } from 'react';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  initials?: string;
  alt: string;
  size?: 'sm' | 'md' | 'lg' | number;
}

export const Avatar: React.FC<AvatarProps> = ({
  src,
  initials,
  alt,
  size = 'md',
  className = '',
  ...props
}) => {
  const [hasError, setHasError] = useState(false);

  const getDimension = () => {
    if (typeof size === 'number') return `${size}px`;
    switch (size) {
      case 'sm':
        return '32px';
      case 'lg':
        return '64px';
      case 'md':
      default:
        return '48px';
    }
  };

  const getFontSize = () => {
    if (typeof size === 'number') return `${size / 2.5}px`;
    switch (size) {
      case 'sm':
        return '0.85rem';
      case 'lg':
        return '1.5rem';
      case 'md':
      default:
        return '1.1rem';
    }
  };

  const dimension = getDimension();
  const fontSize = getFontSize();

  const styles: React.CSSProperties = {
    width: dimension,
    height: dimension,
    fontSize: fontSize,
    lineHeight: dimension,
  };

  const containerClasses = [
    'd-inline-flex',
    'align-items-center',
    'justify-content-center',
    'rounded-circle',
    'bg-secondary-subtle',
    'text-secondary',
    'fw-bold',
    'overflow-hidden',
    'border',
    className
  ].filter(Boolean).join(' ');

  const showImage = src && !hasError;

  return (
    <div
      className={containerClasses}
      style={styles}
      role="img"
      aria-label={alt}
      {...props}
    >
      {showImage ? (
        <img
          src={src}
          alt={alt}
          className="w-100 h-100 object-fit-cover"
          onError={() => setHasError(true)}
        />
      ) : (
        <span aria-hidden="true">{initials || alt.substring(0, 2).toUpperCase()}</span>
      )}
    </div>
  );
};
