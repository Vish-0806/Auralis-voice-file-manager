import React, { createContext, useContext, useState, useEffect } from 'react';

export type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = localStorage.getItem('auralis-theme') as Theme;
    return saved || 'system';
  });

  const setTheme = (newTheme: Theme) => {
    localStorage.setItem('auralis-theme', newTheme);
    setThemeState(newTheme);
  };

  useEffect(() => {
    const root = window.document.documentElement;
    root.removeAttribute('data-theme');
    
    let activeTheme = theme;
    if (theme === 'system') {
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      activeTheme = systemPrefersDark ? 'dark' : 'light';
    }

    root.setAttribute('data-theme', activeTheme);
    root.style.colorScheme = activeTheme;
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
