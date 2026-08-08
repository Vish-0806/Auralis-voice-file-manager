import React from 'react';

export interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: 'row' | 'column';
  gap?: 0 | 1 | 2 | 3 | 4 | 5;
  align?: 'start' | 'end' | 'center' | 'baseline' | 'stretch';
  justify?: 'start' | 'end' | 'center' | 'between' | 'around' | 'evenly';
}

export const Stack: React.FC<StackProps> = ({
  direction = 'column',
  gap,
  align,
  justify,
  className = '',
  children,
  ...props
}) => {
  const classes = [
    'd-flex',
    direction === 'row' ? 'flex-row' : 'flex-column',
    gap !== undefined ? `gap-${gap}` : '',
    align ? `align-items-${align}` : '',
    justify ? `justify-content-${justify}` : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};
