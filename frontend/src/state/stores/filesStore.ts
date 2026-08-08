import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { FilesState } from '../types';

const initialState = {
  currentDirectory: '/',
  selectedFileIds: [],
  searchQuery: '',
  sortMode: 'name' as const,
  sortDirection: 'asc' as const,
  viewMode: 'grid' as const,
  status: 'idle' as const,
  error: null,
};

export const useFilesStore = create<FilesState>()(
  persist(
    (set) => ({
      ...initialState,
      setCurrentDirectory: (value) => set({ currentDirectory: value }),
      setSelectedFileIds: (ids) => set({ selectedFileIds: ids }),
      toggleFileSelection: (id) => set((state) => {
        const isSelected = state.selectedFileIds.includes(id);
        const selectedFileIds = isSelected
          ? state.selectedFileIds.filter((x) => x !== id)
          : [...state.selectedFileIds, id];
        return { selectedFileIds };
      }),
      setSearchQuery: (query) => set({ searchQuery: query }),
      setSortMode: (mode) => set({ sortMode: mode }),
      setSortDirection: (dir) => set({ sortDirection: dir }),
      setViewMode: (mode) => set({ viewMode: mode }),
      setStatus: (status) => set({ status }),
      setError: (error) => set({ error }),
      reset: () => set(initialState),
    }),
    {
      name: 'auralis.files',
      partialize: (state) => ({
        viewMode: state.viewMode,
        sortMode: state.sortMode,
        sortDirection: state.sortDirection,
      }),
    }
  )
);
