import React from 'react';
import { Link } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

export interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items, className = '' }) => {
  return (
    <nav aria-label="breadcrumb" className={className}>
      <ol className="breadcrumb mb-0">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          if (isLast) {
            return (
              <li key={index} className="breadcrumb-item active" aria-current="page">
                {item.label}
              </li>
            );
          }

          return (
            <li key={index} className="breadcrumb-item">
              {item.to ? (
                <Link to={item.to} className="text-decoration-none">
                  {item.label}
                </Link>
              ) : (
                item.label
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
