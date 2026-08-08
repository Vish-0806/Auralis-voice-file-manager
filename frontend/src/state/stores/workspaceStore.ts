import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { WorkspaceState } from '../types';

const initialState = {
  activeWorkspaceId: null,
  openPanels: [],
  activeTab: null,
  status: 'idle' as const,
  error: null,
};

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      ...initialState,
      setActiveWorkspaceId: (value) => set({ activeWorkspaceId: value }),
      setOpenPanels: (panels) => set({ openPanels: panels }),
      togglePanel: (panel) => set((state) => {
        const isOpen = state.openPanels.includes(panel);
        const openPanels = isOpen
          ? state.openPanels.filter((x) => x !== panel)
          : [...state.openPanels, panel];
        return { openPanels };
      }),
      setActiveTab: (tab) => set({ activeTab: tab }),
      setStatus: (status) => set({ status }),
      setError: (error) => set({ error }),
      reset: () => set(initialState),
    }),
    {
      name: 'auralis.workspace',
      partialize: (state) => ({
        activeWorkspaceId: state.activeWorkspaceId,
        openPanels: state.openPanels,
      }),
    }
  )
);
