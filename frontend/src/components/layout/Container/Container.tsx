import React from 'react';

export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  fluid?: boolean | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';
}

export const Container: React.FC<ContainerProps> = ({
  fluid,
  className = '',
  children,
  ...props
}) => {
  const containerClass = fluid
    ? typeof fluid === 'string'
      ? `container-${fluid}`
      : 'container-fluid'
    : 'container';

  return (
    <div className={`${containerClass} ${className}`.trim()} {...props}>
      {children}
    </div>
  );
};
