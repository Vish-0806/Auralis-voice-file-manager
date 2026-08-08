import React from 'react';

export interface RowProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: string | number;
  gap?: 0 | 1 | 2 | 3 | 4 | 5;
}

export const Row: React.FC<RowProps> = ({
  cols,
  gap,
  className = '',
  children,
  ...props
}) => {
  const classes = [
    'row',
    cols ? `row-cols-${cols}` : '',
    gap !== undefined ? `g-${gap}` : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};
