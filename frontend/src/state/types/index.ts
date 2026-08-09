export type AsyncStatus = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState {
  status: AsyncStatus;
  error: string | null;
}

export interface UIState {
  sidebarCollapsed: boolean;
  mobileNavigationOpen: boolean;
  activeModal: string | null;
  globalLoading: boolean;
  
  setSidebarCollapsed: (value: boolean) => void;
  toggleSidebarCollapsed: () => void;
  setMobileNavigationOpen: (value: boolean) => void;
  setActiveModal: (value: string | null) => void;
  setGlobalLoading: (value: boolean) => void;
  reset: () => void;
}

export interface AssistantMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

export interface AssistantState extends AsyncState {
  conversationId: string | null;
  messages: AssistantMessage[];
  isStreaming: boolean;
  
  setConversationId: (value: string | null) => void;
  addMessage: (message: Omit<AssistantMessage, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<AssistantMessage>) => void;
  setStreaming: (value: boolean) => void;
  setStatus: (status: AsyncStatus) => void;
  setError: (error: string | null) => void;
  clearConversation: () => void;
  reset: () => void;
}

export type FileViewMode = 'grid' | 'list';
export type FileSortMode = 'name' | 'date' | 'size';
export type FileSortDirection = 'asc' | 'desc';

export interface FileItem {
  name: string;
  path: string;
  size?: number;
  modified?: string;
  is_directory?: boolean;
  type?: string;
}

export interface FilesState extends AsyncState {
  currentDirectory: string;
  selectedFileIds: string[];
  searchQuery: string;
  sortMode: FileSortMode;
  sortDirection: FileSortDirection;
  viewMode: FileViewMode;
  files: FileItem[];
  
  setCurrentDirectory: (value: string) => void;
  setSelectedFileIds: (ids: string[]) => void;
  toggleFileSelection: (id: string) => void;
  setSearchQuery: (query: string) => void;
  setSortMode: (mode: FileSortMode) => void;
  setSortDirection: (dir: FileSortDirection) => void;
  setViewMode: (mode: FileViewMode) => void;
  setFiles: (files: FileItem[]) => void;
  setStatus: (status: AsyncStatus) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export interface WorkspaceState extends AsyncState {
  activeWorkspaceId: string | null;
  openPanels: string[];
  activeTab: string | null;
  openTabs: string[];
  
  setActiveWorkspaceId: (value: string | null) => void;
  setOpenPanels: (panels: string[]) => void;
  togglePanel: (panel: string) => void;
  setActiveTab: (tab: string | null) => void;
  openTab: (tab: string) => void;
  closeTab: (tab: string) => void;
  setStatus: (status: AsyncStatus) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export type UiDensityMode = 'compact' | 'normal' | 'cozy';

export interface AccessibilityPreferences {
  highContrast: boolean;
  screenReaderOptimized: boolean;
}

export interface SettingsState {
  uiDensity: UiDensityMode;
  accessibilityPreference: AccessibilityPreferences;
  
  setUiDensity: (value: UiDensityMode) => void;
  setAccessibilityPreference: (prefs: Partial<AccessibilityPreferences>) => void;
  reset: () => void;
}
