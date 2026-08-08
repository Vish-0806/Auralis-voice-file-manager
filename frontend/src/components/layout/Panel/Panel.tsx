import React from 'react';

export interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 0 | 1 | 2 | 3 | 4 | 5;
  shadow?: boolean | 'sm' | 'lg';
  bordered?: boolean;
}

export const Panel: React.FC<PanelProps> = ({
  padding = 3,
  shadow = false,
  bordered = true,
  className = '',
  children,
  ...props
}) => {
  const classes = [
    'bg-body',
    'rounded',
    padding !== undefined ? `p-${padding}` : '',
    bordered ? 'border' : '',
    shadow === true ? 'shadow' : shadow ? `shadow-${shadow}` : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};
