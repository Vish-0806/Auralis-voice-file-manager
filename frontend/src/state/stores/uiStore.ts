import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UIState } from '../types';

const initialState = {
  sidebarCollapsed: false,
  mobileNavigationOpen: false,
  activeModal: null,
  globalLoading: false,
};

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      ...initialState,
      setSidebarCollapsed: (value) => set({ sidebarCollapsed: value }),
      toggleSidebarCollapsed: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setMobileNavigationOpen: (value) => set({ mobileNavigationOpen: value }),
      setActiveModal: (value) => set({ activeModal: value }),
      setGlobalLoading: (value) => set({ globalLoading: value }),
      reset: () => set(initialState),
    }),
    {
      name: 'auralis.ui',
      partialize: (state) => ({ sidebarCollapsed: state.sidebarCollapsed }),
    }
  )
);
