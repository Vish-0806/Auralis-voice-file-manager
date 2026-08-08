import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ThemeProvider, useTheme } from '../../src/theme/ThemeProvider';
import { ThemeToggle } from '../../src/components/common/ThemeToggle/ThemeToggle';

const ThemeConsumer = () => {
  const { theme, setTheme, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button onClick={() => setTheme('light')} data-testid="set-light">Light</button>
      <button onClick={() => setTheme('dark')} data-testid="set-dark">Dark</button>
      <button onClick={() => setTheme('system')} data-testid="set-system">System</button>
      <button onClick={toggleTheme} data-testid="toggle-theme">Toggle</button>
    </div>
  );
};

describe('Theme Design System Runtime Tests', () => {
  let matchMediaMock: any;
  let mediaListeners: Array<() => void> = [];

  beforeEach(() => {
    localStorage.clear();
    mediaListeners = [];

    matchMediaMock = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn((listener: any) => mediaListeners.push(listener)),
      removeListener: vi.fn(),
      addEventListener: vi.fn((_event: string, listener: any) => mediaListeners.push(listener)),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
    vi.stubGlobal('matchMedia', matchMediaMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.style.colorScheme = '';
  });

  it('1. ThemeProvider renders children correctly', () => {
    render(
      <ThemeProvider>
        <div data-testid="child">Test Content</div>
      </ThemeProvider>
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('2. Default theme is system', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('theme-value')).toHaveTextContent('system');
  });

  it('3. setTheme changes context theme value', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    const themeSpan = screen.getByTestId('theme-value');
    expect(themeSpan).toHaveTextContent('system');

    fireEvent.click(screen.getByTestId('set-dark'));
    expect(themeSpan).toHaveTextContent('dark');

    fireEvent.click(screen.getByTestId('set-light'));
    expect(themeSpan).toHaveTextContent('light');
  });

  it('4. toggleTheme cycles light -> dark -> system -> light', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    const themeSpan = screen.getByTestId('theme-value');
    
    fireEvent.click(screen.getByTestId('toggle-theme'));
    expect(themeSpan).toHaveTextContent('light');

    fireEvent.click(screen.getByTestId('toggle-theme'));
    expect(themeSpan).toHaveTextContent('dark');

    fireEvent.click(screen.getByTestId('toggle-theme'));
    expect(themeSpan).toHaveTextContent('system');
  });

  it('5 & 11. Theme change updates document root attributes and styling', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(document.documentElement.style.colorScheme).toBe('light');

    fireEvent.click(screen.getByTestId('set-dark'));
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(document.documentElement.style.colorScheme).toBe('dark');
  });

  it('8. Theme preference persists in localStorage', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByTestId('set-dark'));
    expect(localStorage.getItem('auralis.theme')).toBe('dark');

    fireEvent.click(screen.getByTestId('set-system'));
    expect(localStorage.getItem('auralis.theme')).toBe('system');
  });

  it('9. Invalid or corrupted localStorage theme falls back safely', () => {
    localStorage.setItem('auralis.theme', 'corrupted-mode');
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    expect(screen.getByTestId('theme-value')).toHaveTextContent('system');
  });

  it('10. System preference scheme change triggers updates', () => {
    matchMediaMock.mockImplementation((query: string) => ({
      matches: true,
      media: query,
      addListener: vi.fn((listener: any) => mediaListeners.push(listener)),
      removeListener: vi.fn(),
      addEventListener: vi.fn((_event: string, listener: any) => mediaListeners.push(listener)),
      removeEventListener: vi.fn(),
    }));

    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );

    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');

    matchMediaMock.mockImplementation((query: string) => ({
      matches: false,
      media: query,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));

    act(() => {
      mediaListeners.forEach((listener) => listener());
    });

    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('12 & 13. ThemeToggle accessibility and toggling mechanism', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const toggleBtn = screen.getByRole('button', { name: /toggle theme/i });
    expect(toggleBtn).toBeInTheDocument();
    expect(toggleBtn).toHaveAttribute('title');

    fireEvent.click(toggleBtn);
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });
});
