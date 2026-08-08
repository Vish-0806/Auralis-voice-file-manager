import React from 'react';
import { useTheme } from '../../../theme/ThemeProvider';
import { IconButton } from '../IconButton';

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  const getIcon = () => {
    switch (theme) {
      case 'light':
        return 'bi-sun-fill text-warning';
      case 'dark':
        return 'bi-moon-stars-fill text-primary';
      default:
        return 'bi-laptop text-secondary';
    }
  };

  const getLabel = () => {
    switch (theme) {
      case 'light':
        return 'Light Theme. Click to cycle to Dark.';
      case 'dark':
        return 'Dark Theme. Click to cycle to System.';
      default:
        return 'System Preference Theme. Click to cycle to Light.';
    }
  };

  return (
    <IconButton
      icon={getIcon()}
      onClick={toggleTheme}
      aria-label="Toggle Theme"
      title={getLabel()}
      className="theme-toggle-btn"
    />
  );
};
