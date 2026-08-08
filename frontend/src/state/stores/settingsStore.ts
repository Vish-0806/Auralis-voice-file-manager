import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { SettingsState } from '../types';

const initialState = {
  uiDensity: 'normal' as const,
  accessibilityPreference: {
    highContrast: false,
    screenReaderOptimized: false,
  },
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...initialState,
      setUiDensity: (value) => set({ uiDensity: value }),
      setAccessibilityPreference: (prefs) => set((state) => ({
        accessibilityPreference: {
          ...state.accessibilityPreference,
          ...prefs,
        },
      })),
      reset: () => set(initialState),
    }),
    {
      name: 'auralis.settings',
    }
  )
);
