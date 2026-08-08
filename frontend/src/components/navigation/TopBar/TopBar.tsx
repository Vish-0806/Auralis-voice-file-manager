import React from 'react';

export interface TopBarProps extends React.HTMLAttributes<HTMLElement> {
  title?: string;
}

export const TopBar: React.FC<TopBarProps> = ({
  title,
  className = '',
  children,
  ...props
}) => {
  return (
    <header
      className={`navbar navbar-expand-lg bg-body border-bottom px-4 py-2 d-flex justify-content-between align-items-center ${className}`.trim()}
      {...props}
    >
      {title && <span className="navbar-brand mb-0 h1 fw-semibold">{title}</span>}
      <div className="d-flex align-items-center gap-3">
        {children}
      </div>
    </header>
  );
};
