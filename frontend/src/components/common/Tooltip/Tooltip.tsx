import React from 'react';
import './Tooltip.css';

export interface TooltipProps {
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  children: React.ReactElement;
}

/**
 * A lightweight CSS-based hover tooltip.
 * NOTE: Does not use heavy positioning engines (like Popper.js).
 * Placement is done using simple CSS relative alignment.
 */
export const Tooltip: React.FC<TooltipProps> = ({
  content,
  position = 'top',
  children
}) => {
  return (
    <div
      className={`auralis-tooltip-container auralis-tooltip-${position}`}
      data-tooltip={content}
      role="tooltip"
    >
      {children}
    </div>
  );
};
