import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../theme/ThemeProvider';
import { ErrorBoundary } from '../components/common/ErrorBoundary/ErrorBoundary';
import { authService } from '../services/auth/authService';

interface ProvidersProps {
  children: React.ReactNode;
}

export const Providers: React.FC<ProvidersProps> = ({ children }) => {
  // Centralized authentication session bootstrapping
  if (!authService.isAuthenticated()) {
    authService.loginPlaceholder('user@auralis.local', 'Default User');
  }

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
};
