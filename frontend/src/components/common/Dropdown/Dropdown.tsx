import React, { useState, useRef, useEffect } from 'react';

export interface DropdownItem {
  key: string;
  label: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
}

export interface DropdownProps {
  label: React.ReactNode;
  items: DropdownItem[];
  variant?: 'primary' | 'secondary' | 'light' | 'dark' | 'outline-primary' | 'outline-secondary';
  align?: 'left' | 'right';
}

export const Dropdown: React.FC<DropdownProps> = ({
  label,
  items,
  variant = 'secondary',
  align = 'left'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const toggle = () => setIsOpen(!isOpen);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="dropdown d-inline-block" ref={dropdownRef}>
      <button
        className={`btn btn-${variant} dropdown-toggle`}
        type="button"
        aria-expanded={isOpen}
        onClick={toggle}
      >
        {label}
      </button>
      <ul
        className={`dropdown-menu ${isOpen ? 'show' : ''} ${
          align === 'right' ? 'dropdown-menu-end' : ''
        }`}
        style={isOpen ? { display: 'block', position: 'absolute', right: align === 'right' ? 0 : 'auto' } : undefined}
      >
        {items.map((item) => (
          <li key={item.key}>
            <button
              className={`dropdown-item ${item.disabled ? 'disabled' : ''}`}
              type="button"
              disabled={item.disabled}
              onClick={() => {
                if (!item.disabled) {
                  item.onClick?.();
                  setIsOpen(false);
                }
              }}
            >
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};
