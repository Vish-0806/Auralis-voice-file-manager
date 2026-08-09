import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { WorkspaceState } from '../types';

const initialState = {
  activeWorkspaceId: null,
  openPanels: [],
  activeTab: null,
  openTabs: [],
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
      openTab: (tab) => set((state) => {
        const openTabs = state.openTabs.includes(tab)
          ? state.openTabs
          : [...state.openTabs, tab];
        return { openTabs, activeTab: tab };
      }),
      closeTab: (tab) => set((state) => {
        const openTabs = state.openTabs.filter((x) => x !== tab);
        let activeTab = state.activeTab;
        if (activeTab === tab) {
          activeTab = openTabs.length > 0 ? openTabs[openTabs.length - 1] : null;
        }
        return { openTabs, activeTab };
      }),
      setStatus: (status) => set({ status }),
      setError: (error) => set({ error }),
      reset: () => set(initialState),
    }),
    {
      name: 'auralis.workspace',
      partialize: (state) => ({
        activeWorkspaceId: state.activeWorkspaceId,
        openPanels: state.openPanels,
        openTabs: state.openTabs,
        activeTab: state.activeTab,
      }),
    }
  )
);
