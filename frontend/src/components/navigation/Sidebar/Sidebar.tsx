import React from 'react';

export interface SidebarProps extends React.HTMLAttributes<HTMLElement> {
  brandName?: string;
  brandIcon?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  brandName = 'Auralis',
  brandIcon = 'bi-soundwave',
  className = '',
  children,
  ...props
}) => {
  return (
    <aside
      className={`d-flex flex-column flex-shrink-0 p-3 bg-body-tertiary border-end ${className}`.trim()}
      style={{ width: '280px', height: '100vh' }}
      {...props}
    >
      <div className="d-flex align-items-center gap-2 mb-3 mb-md-0 me-md-auto link-body-emphasis text-decoration-none">
        {brandIcon && <i className={`bi ${brandIcon} text-primary fs-3`} />}
        <span className="fs-4 fw-bold">{brandName}</span>
      </div>
      <hr />
      <nav className="nav nav-pills flex-column mb-auto gap-1">
        {children}
      </nav>
    </aside>
  );
};
