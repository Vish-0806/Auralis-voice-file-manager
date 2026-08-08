import React from 'react';
import { NavLink } from 'react-router-dom';

export interface NavItemProps {
  to: string;
  icon?: string;
  label: string;
  badge?: string | number;
  badgeVariant?: string;
  disabled?: boolean;
  className?: string;
  onClick?: () => void;
}

export const NavItem: React.FC<NavItemProps> = ({
  to,
  icon,
  label,
  badge,
  badgeVariant = 'primary',
  disabled = false,
  className = '',
  onClick
}) => {
  const baseClasses = 'nav-link d-flex align-items-center gap-2 rounded px-3 py-2 text-decoration-none';

  if (disabled) {
    return (
      <span className={`${baseClasses} disabled text-muted ${className}`.trim()}>
        {icon && <i className={`bi ${icon}`} />}
        <span>{label}</span>
        {badge !== undefined && (
          <span className={`badge bg-${badgeVariant} ms-auto`}>{badge}</span>
        )}
      </span>
    );
  }

  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        [
          baseClasses,
          isActive ? 'active bg-primary text-white' : 'text-body',
          className
        ].filter(Boolean).join(' ')
      }
    >
      {icon && <i className={`bi ${icon}`} />}
      <span>{label}</span>
      {badge !== undefined && (
        <span className={`badge bg-${badgeVariant} ms-auto`}>{badge}</span>
      )}
    </NavLink>
  );
};
