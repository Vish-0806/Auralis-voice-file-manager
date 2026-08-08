import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  clickable?: boolean;
}

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', children, ...props }) => (
  <div className={`card-header d-flex justify-content-between align-items-center ${className}`.trim()} {...props}>
    {children}
  </div>
);

export const CardBody: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', children, ...props }) => (
  <div className={`card-body ${className}`.trim()} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className = '', children, ...props }) => (
  <div className={`card-footer ${className}`.trim()} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className = '', children, ...props }) => (
  <h5 className={`card-title ${className}`.trim()} {...props}>
    {children}
  </h5>
);

export const CardSubtitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className = '', children, ...props }) => (
  <h6 className={`card-subtitle text-muted mb-2 ${className}`.trim()} {...props}>
    {children}
  </h6>
);

const CardComponent: React.FC<CardProps> = ({ clickable = false, className = '', children, ...props }) => {
  const classes = [
    'card',
    clickable ? 'card-clickable border-primary-hover shadow-sm-hover transition-all' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={classes} style={clickable ? { cursor: 'pointer' } : undefined} {...props}>
      {children}
    </div>
  );
};

export const Card = Object.assign(CardComponent, {
  Header: CardHeader,
  Body: CardBody,
  Footer: CardFooter,
  Title: CardTitle,
  Subtitle: CardSubtitle
});
