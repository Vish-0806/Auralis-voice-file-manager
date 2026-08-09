import { UIState, AssistantState, FilesState, WorkspaceState, SettingsState } from '../types';

// UI Selectors
export const selectSidebarCollapsed = (state: UIState) => state.sidebarCollapsed;
export const selectMobileNavigationOpen = (state: UIState) => state.mobileNavigationOpen;
export const selectActiveModal = (state: UIState) => state.activeModal;
export const selectGlobalLoading = (state: UIState) => state.globalLoading;

// Assistant Selectors
export const selectConversationId = (state: AssistantState) => state.conversationId;
export const selectAssistantMessages = (state: AssistantState) => state.messages;
export const selectIsAssistantStreaming = (state: AssistantState) => state.isStreaming;
export const selectAssistantStatus = (state: AssistantState) => state.status;
export const selectAssistantError = (state: AssistantState) => state.error;

// Files Selectors
export const selectCurrentDirectory = (state: FilesState) => state.currentDirectory;
export const selectSelectedFileIds = (state: FilesState) => state.selectedFileIds;
export const selectSelectedFileCount = (state: FilesState) => state.selectedFileIds.length;
export const selectSearchQuery = (state: FilesState) => state.searchQuery;
export const selectFileSortMode = (state: FilesState) => state.sortMode;
export const selectFileSortDirection = (state: FilesState) => state.sortDirection;
export const selectFileViewMode = (state: FilesState) => state.viewMode;
export const selectFilesList = (state: FilesState) => state.files;
export const selectFilesStatus = (state: FilesState) => state.status;
export const selectFilesError = (state: FilesState) => state.error;

// Workspace Selectors
export const selectActiveWorkspaceId = (state: WorkspaceState) => state.activeWorkspaceId;
export const selectOpenPanels = (state: WorkspaceState) => state.openPanels;
export const selectActiveTab = (state: WorkspaceState) => state.activeTab;
export const selectOpenTabs = (state: WorkspaceState) => state.openTabs;
export const selectWorkspaceStatus = (state: WorkspaceState) => state.status;
export const selectWorkspaceError = (state: WorkspaceState) => state.error;

// Settings Selectors
export const selectUiDensity = (state: SettingsState) => state.uiDensity;
export const selectAccessibilityPreference = (state: SettingsState) => state.accessibilityPreference;
