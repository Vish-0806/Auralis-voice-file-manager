import React from 'react';

export interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  breadcrumbs?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  actions,
  breadcrumbs,
  className = ''
}) => {
  return (
    <div className={`d-flex flex-column gap-2 pb-3 mb-4 border-bottom ${className}`.trim()}>
      {breadcrumbs && <div className="mb-1">{breadcrumbs}</div>}
      <div className="d-flex align-items-md-center justify-content-between gap-3 flex-column flex-md-row">
        <div>
          <h1 className="h2 mb-1 fw-bold">{title}</h1>
          {description && <p className="text-muted mb-0">{description}</p>}
        </div>
        {actions && <div className="d-flex gap-2 align-items-center">{actions}</div>}
      </div>
    </div>
  );
};
