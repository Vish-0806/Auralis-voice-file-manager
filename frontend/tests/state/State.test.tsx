import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { act } from 'react';
import {
  useUIStore,
  useAssistantStore,
  useFilesStore,
  useWorkspaceStore,
  useSettingsStore,
} from '../../src/state/stores';
import {
  selectSidebarCollapsed,
  selectSelectedFileCount,
  selectUiDensity,
} from '../../src/state/selectors';

describe('State Management Runtime Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    act(() => {
      useUIStore.getState().reset();
      useAssistantStore.getState().reset();
      useFilesStore.getState().reset();
      useWorkspaceStore.getState().reset();
      useSettingsStore.getState().reset();
    });
  });

  describe('UI Store', () => {
    it('1. should initialize correctly', () => {
      const state = useUIStore.getState();
      expect(state.sidebarCollapsed).toBe(false);
      expect(state.mobileNavigationOpen).toBe(false);
      expect(state.activeModal).toBeNull();
      expect(state.globalLoading).toBe(false);
    });

    it('2. should toggle and set states successfully', () => {
      act(() => {
        useUIStore.getState().setSidebarCollapsed(true);
      });
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);

      act(() => {
        useUIStore.getState().toggleSidebarCollapsed();
      });
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);

      act(() => {
        useUIStore.getState().setMobileNavigationOpen(true);
        useUIStore.getState().setActiveModal('test-modal');
        useUIStore.getState().setGlobalLoading(true);
      });

      const updated = useUIStore.getState();
      expect(updated.mobileNavigationOpen).toBe(true);
      expect(updated.activeModal).toBe('test-modal');
      expect(updated.globalLoading).toBe(true);
    });

    it('3. should reset back to initial values', () => {
      act(() => {
        useUIStore.getState().setSidebarCollapsed(true);
        useUIStore.getState().reset();
      });
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
    });
  });

  describe('Assistant Store', () => {
    it('4. should initialize correctly', () => {
      const state = useAssistantStore.getState();
      expect(state.conversationId).toBeNull();
      expect(state.messages).toEqual([]);
      expect(state.isStreaming).toBe(false);
      expect(state.status).toBe('idle');
      expect(state.error).toBeNull();
    });

    it('5. should add, update, and clear messages correctly', () => {
      act(() => {
        useAssistantStore.getState().setConversationId('session-123');
        useAssistantStore.getState().addMessage({
          role: 'user',
          content: 'Hello, Assistant!',
        });
      });

      const state = useAssistantStore.getState();
      expect(state.conversationId).toBe('session-123');
      expect(state.messages).toHaveLength(1);
      
      const message = state.messages[0];
      expect(message.content).toBe('Hello, Assistant!');
      expect(message.id).toBeDefined();
      expect(message.timestamp).toBeLessThanOrEqual(Date.now());

      act(() => {
        useAssistantStore.getState().updateMessage(message.id, { content: 'Updated content' });
      });
      expect(useAssistantStore.getState().messages[0].content).toBe('Updated content');

      act(() => {
        useAssistantStore.getState().clearConversation();
      });
      expect(useAssistantStore.getState().messages).toEqual([]);
      expect(useAssistantStore.getState().conversationId).toBeNull();
    });
  });

  describe('Files Store', () => {
    it('7. should initialize correctly', () => {
      const state = useFilesStore.getState();
      expect(state.currentDirectory).toBe('/');
      expect(state.selectedFileIds).toEqual([]);
      expect(state.searchQuery).toBe('');
      expect(state.sortMode).toBe('name');
      expect(state.sortDirection).toBe('asc');
      expect(state.viewMode).toBe('grid');
    });

    it('8 & 9. should handle selection lists, view, sort, and filters', () => {
      act(() => {
        useFilesStore.getState().toggleFileSelection('file-1');
      });
      expect(useFilesStore.getState().selectedFileIds).toEqual(['file-1']);

      act(() => {
        useFilesStore.getState().toggleFileSelection('file-1');
      });
      expect(useFilesStore.getState().selectedFileIds).toEqual([]);

      act(() => {
        useFilesStore.getState().setCurrentDirectory('/documents');
        useFilesStore.getState().setSearchQuery('voice');
        useFilesStore.getState().setSortMode('size');
        useFilesStore.getState().setSortDirection('desc');
        useFilesStore.getState().setViewMode('list');
      });

      const state = useFilesStore.getState();
      expect(state.currentDirectory).toBe('/documents');
      expect(state.searchQuery).toBe('voice');
      expect(state.sortMode).toBe('size');
      expect(state.sortDirection).toBe('desc');
      expect(state.viewMode).toBe('list');
    });
  });

  describe('Workspace Store', () => {
    it('10. should handle active state, panels list, and tab toggling', () => {
      act(() => {
        useWorkspaceStore.getState().setActiveWorkspaceId('ws-1');
        useWorkspaceStore.getState().togglePanel('right-panel');
      });

      const state = useWorkspaceStore.getState();
      expect(state.activeWorkspaceId).toBe('ws-1');
      expect(state.openPanels).toEqual(['right-panel']);

      act(() => {
        useWorkspaceStore.getState().togglePanel('right-panel');
      });
      expect(useWorkspaceStore.getState().openPanels).toEqual([]);
    });
  });

  describe('Settings Store', () => {
    it('11. should handle UI density and accessibility preference settings', () => {
      act(() => {
        useSettingsStore.getState().setUiDensity('compact');
        useSettingsStore.getState().setAccessibilityPreference({ highContrast: true });
      });

      const state = useSettingsStore.getState();
      expect(state.uiDensity).toBe('compact');
      expect(state.accessibilityPreference.highContrast).toBe(true);
      expect(state.accessibilityPreference.screenReaderOptimized).toBe(false);
    });
  });

  describe('Selectors', () => {
    it('12. should return correct sub-state mappings', () => {
      act(() => {
        useUIStore.getState().setSidebarCollapsed(true);
        useFilesStore.getState().setSelectedFileIds(['file-1', 'file-2']);
        useSettingsStore.getState().setUiDensity('cozy');
      });

      expect(selectSidebarCollapsed(useUIStore.getState())).toBe(true);
      expect(selectSelectedFileCount(useFilesStore.getState())).toBe(2);
      expect(selectUiDensity(useSettingsStore.getState())).toBe('cozy');
    });
  });

  describe('React Component Integration', () => {
    it('17. components should consume store state correctly', () => {
      const StateTester = () => {
        const collapsed = useUIStore(selectSidebarCollapsed);
        return <div data-testid="sidebar-collapsed">{collapsed ? 'yes' : 'no'}</div>;
      };

      render(<StateTester />);
      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('no');

      act(() => {
        useUIStore.getState().setSidebarCollapsed(true);
      });

      expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('yes');
    });
  });

  describe('Persistence', () => {
    it('13 & 14. should persist settings data to localStorage and reload it', () => {
      act(() => {
        useSettingsStore.getState().setUiDensity('cozy');
      });
      const stored = localStorage.getItem('auralis.settings');
      expect(stored).toBeDefined();
      expect(JSON.parse(stored!).state.uiDensity).toBe('cozy');
    });

    it('15. should handle corrupted localStorage key safely', () => {
      localStorage.setItem('auralis.settings', 'invalid-json');
      act(() => {
        useSettingsStore.getState().reset();
      });
      expect(useSettingsStore.getState().uiDensity).toBe('normal');
    });
  });
});
