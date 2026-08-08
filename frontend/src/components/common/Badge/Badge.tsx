import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info' | 'light' | 'dark';
  pill?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'primary',
  pill = false,
  className = '',
  children,
  ...props
}) => {
  const classes = [
    'badge',
    `bg-${variant}`,
    pill ? 'rounded-pill' : '',
    variant === 'light' ? 'text-dark' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <span className={classes} {...props}>
      {children}
    </span>
  );
};
