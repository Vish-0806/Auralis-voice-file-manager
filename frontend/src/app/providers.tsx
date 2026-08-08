import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../theme/ThemeProvider';

interface ProvidersProps {
  children: React.ReactNode;
}

export const Providers: React.FC<ProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </BrowserRouter>
  );
};
