export interface ColorTheme {
  background: string;
  backgroundSubtle: string;
  backgroundElevated: string;
  backgroundMuted: string;
  surface: string;
  surfaceHover: string;
  surfaceActive: string;
  surfaceElevated: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textDisabled: string;
  textInverse: string;
  border: string;
  borderSubtle: string;
  borderStrong: string;
  brand: string;
  brandHover: string;
  brandActive: string;
  brandSubtle: string;
  brandContrast: string;
  success: string;
  successSubtle: string;
  warning: string;
  warningSubtle: string;
  danger: string;
  dangerSubtle: string;
  info: string;
  infoSubtle: string;
}

export const lightTheme: ColorTheme = {
  background: '#f8f9fa',
  backgroundSubtle: '#ffffff',
  backgroundElevated: '#ffffff',
  backgroundMuted: '#e9ecef',
  surface: '#ffffff',
  surfaceHover: '#f1f3f5',
  surfaceActive: '#e9ecef',
  surfaceElevated: '#ffffff',
  textPrimary: '#212529',
  textSecondary: '#495057',
  textMuted: '#6c757d',
  textDisabled: '#adb5bd',
  textInverse: '#ffffff',
  border: '#dee2e6',
  borderSubtle: '#f1f3f5',
  borderStrong: '#adb5bd',
  brand: '#0d6efd',
  brandHover: '#0b5ed7',
  brandActive: '#0a58ca',
  brandSubtle: '#e2eafd',
  brandContrast: '#ffffff',
  success: '#198754',
  successSubtle: '#d1e7dd',
  warning: '#ffc107',
  warningSubtle: '#fff3cd',
  danger: '#dc3545',
  dangerSubtle: '#f8d7da',
  info: '#0dcaf0',
  infoSubtle: '#cff4fc',
};

export const darkTheme: ColorTheme = {
  background: '#121212',
  backgroundSubtle: '#1e1e1e',
  backgroundElevated: '#2d2d2d',
  backgroundMuted: '#252525',
  surface: '#1e1e1e',
  surfaceHover: '#2d2d2d',
  surfaceActive: '#3d3d3d',
  surfaceElevated: '#2d2d2d',
  textPrimary: '#f8f9fa',
  textSecondary: '#e9ecef',
  textMuted: '#adb5bd',
  textDisabled: '#6c757d',
  textInverse: '#212529',
  border: '#2d2d2d',
  borderSubtle: '#252525',
  borderStrong: '#495057',
  brand: '#3b82f6',
  brandHover: '#60a5fa',
  brandActive: '#2563eb',
  brandSubtle: '#1d4ed8',
  brandContrast: '#ffffff',
  success: '#22c55e',
  successSubtle: '#052e16',
  warning: '#eab308',
  warningSubtle: '#422006',
  danger: '#ef4444',
  dangerSubtle: '#450a0a',
  info: '#3b82f6',
  infoSubtle: '#1e3a8a',
};

export const themes = {
  light: lightTheme,
  dark: darkTheme,
};
