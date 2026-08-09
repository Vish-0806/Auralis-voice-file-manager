import React, { act } from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../../src/app';
import { useWorkspaceStore } from '../../src/state/stores/workspaceStore';
import { useFilesStore } from '../../src/state/stores/filesStore';
import { useVoiceStore } from '../../src/voice/state/voiceStore';
import { syncService } from '../../src/services/synchronization/synchronizationService';
import { assistantService } from '../../src/services/api/assistantService';
import { filesService } from '../../src/services/api/filesService';

// Mock navigator.mediaDevices for JSDOM mic tests
const mockStream = {
  getTracks: () => [{ stop: vi.fn() }],
};
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  configurable: true,
  value: {
    getUserMedia: vi.fn().mockResolvedValue(mockStream),
  },
});

// Mock voiceService
vi.mock('../../src/services/api/voiceService', () => ({
  voiceService: {
    listenVoice: vi.fn().mockResolvedValue({
      status: 'success',
      recognized_text: 'mock command',
      response: 'processed command',
    }),
    startListener: vi.fn().mockResolvedValue({ status: 'started' }),
    stopListener: vi.fn().mockResolvedValue({ status: 'stopped' }),
    getListenerStatus: vi.fn().mockResolvedValue({ active: false }),
  },
  default: {
    listenVoice: vi.fn().mockResolvedValue({
      status: 'success',
      recognized_text: 'mock command',
      response: 'processed command',
    }),
    startListener: vi.fn().mockResolvedValue({ status: 'started' }),
    stopListener: vi.fn().mockResolvedValue({ status: 'stopped' }),
    getListenerStatus: vi.fn().mockResolvedValue({ active: false }),
  }
}));


let shouldDashboardCrash = false;

vi.mock('../../src/pages/dashboard/DashboardPage', async (importActual) => {
  const actual: any = await importActual();
  const MockedDashboard = (props: any) => {
    if (shouldDashboardCrash) {
      throw new Error('Dashboard render crash');
    }
    const Target = actual.DashboardPage || actual.default;
    return React.createElement(Target, props);
  };
  return {
    ...actual,
    DashboardPage: MockedDashboard,
    default: MockedDashboard,
  };
});

describe('Auralis V2 Integration Workflows (Stage 20 Production Certification)', () => {
  beforeEach(() => {
    // Reset stores
    useWorkspaceStore.getState().reset();
    useFilesStore.getState().reset();
    useVoiceStore.getState().reset();
    shouldDashboardCrash = false;
    syncService.stop();
    window.history.pushState({}, 'Home', '/');
    vi.clearAllMocks();

    // Default mock implementation to return document.txt at root directory
    (filesService.searchFiles as any).mockImplementation(() => Promise.resolve([
      { name: 'document.txt', path: 'C:/Users/Vishal/document.txt', size: 1024, modified: '2026-08-09T10:00:00Z' }
    ]));
  });

  it('WORKFLOW 1: Application startup -> Dashboard -> Navigation -> Settings -> Theme toggle -> Return Dashboard', async () => {
    render(<App />);
    const user = userEvent.setup();

    // Verify application startup and landing on Dashboard
    expect(await screen.findByText('Voice File Manager')).toBeInTheDocument();
    expect(await screen.findByText('Quick Access Shortcuts')).toBeInTheDocument();
    expect(await screen.findByText('Backend Service Status')).toBeInTheDocument();

    // Navigate to Settings
    const settingsLink = screen.getAllByRole('link', { name: /settings/i })[0];
    await user.click(settingsLink);
    expect(await screen.findByText('Application Preferences')).toBeInTheDocument();

    // Theme toggle interaction
    const themeToggleBtn = screen.getByRole('button', { name: /Toggle Theme/i });
    await user.click(themeToggleBtn);

    // Return to Dashboard
    const dashboardLink = screen.getAllByRole('link', { name: /dashboard/i })[0];
    await user.click(dashboardLink);
    expect(await screen.findByText('Quick Access Shortcuts')).toBeInTheDocument();
  });

  it('WORKFLOW 2: Dashboard -> Files -> Search files -> Open file -> Workspace -> Open tab -> Close tab', async () => {
    render(<App />);
    const user = userEvent.setup();

    // Nav to Files page
    const filesLink = screen.getAllByRole('link', { name: /file manager/i })[0];
    await user.click(filesLink);
    expect(await screen.findByText('Sort by:')).toBeInTheDocument();

    // Search files input interaction
    const searchInput = screen.getByPlaceholderText(/search staged files/i);
    await user.type(searchInput, 'doc');

    // Double click file item to trigger opening in workspace
    const fileRow = await screen.findByText('document.txt');
    expect(fileRow).toBeInTheDocument();
    await user.dblClick(fileRow);

    // Navigate to Workspace to view active tab
    const workspaceLink = screen.getAllByRole('link', { name: /workspace/i })[0];
    await user.click(workspaceLink);

    // Verify redirection to Workspace and active opened tab
    expect(await screen.findByText('Directory Tree')).toBeInTheDocument();
    expect(await screen.findByText('document.txt')).toBeInTheDocument();

    // Close the document tab
    const closeTabBtn = screen.getByLabelText(/close document.txt tab/i);
    await user.click(closeTabBtn);
    expect(screen.queryByRole('tab', { name: 'document.txt' })).not.toBeInTheDocument();
  });

  it('WORKFLOW 3: Dashboard -> Assistant -> Voice control -> Listening -> Transcript update -> Command response', async () => {
    render(<App />);
    const user = userEvent.setup();

    // Navigate to Assistant
    const assistantLink = screen.getAllByRole('link', { name: /assistant/i })[0];
    await user.click(assistantLink);
    expect(await screen.findByText('Assistant Hub')).toBeInTheDocument();

    // Toggle mic / start voice listening
    const micBtn = screen.getByRole('button', { name: /Start Listening/i });
    await user.click(micBtn);

    // Verify speech completion and recognized transcript text
    expect(await screen.findByText('Completed')).toBeInTheDocument();
    expect(await screen.findByText('mock command')).toBeInTheDocument();
  });

  it('WORKFLOW 4: Workspace -> Search -> Sort -> Grid/List -> Open preview -> Persist tab', async () => {
    useWorkspaceStore.getState().setOpenPanels(['sidebar', 'preview']);

    render(<App />);
    const user = userEvent.setup();

    // Nav to Workspace
    const workspaceLink = screen.getAllByRole('link', { name: /workspace/i })[0];
    await user.click(workspaceLink);
    expect(await screen.findByText('Directory Tree')).toBeInTheDocument();

    // Switch list/grid view mode
    const gridModeBtn = screen.getByRole('button', { name: /Grid View/i });
    await user.click(gridModeBtn);
    expect(useFilesStore.getState().viewMode).toBe('grid');

    // Change sorting field
    const sortSelect = screen.getByRole('combobox');
    await user.selectOptions(sortSelect, 'name');
    expect(useFilesStore.getState().sortMode).toBe('name');

    // Search query interaction
    const searchInput = screen.getByPlaceholderText(/search staged files/i);
    await user.type(searchInput, 'doc');
    await new Promise(r => setTimeout(r, 500));
    expect(useFilesStore.getState().searchQuery).toBe('doc');

    // Open file tab
    const fileItem = await screen.findByText('document.txt');
    await user.dblClick(fileItem);

    // Verify preview card shows up
    expect(await screen.findByText('document.txt')).toBeInTheDocument();
    expect(screen.getAllByText('Staging Preview: document.txt')[0]).toBeInTheDocument();
  });

  it('WORKFLOW 5: Backend unavailable -> Application still loads -> Dashboard shows error state -> Navigation still works', async () => {
    // Force API service methods rejection
    (assistantService.getHealth as any).mockImplementation(() => Promise.reject(new Error('Backend Unavailable')));
    (assistantService.getStatus as any).mockImplementation(() => Promise.reject(new Error('Backend Unavailable')));

    render(<App />);

    // Application shell layout loads successfully
    expect(await screen.findByText('Voice File Manager')).toBeInTheDocument();

    // Status indicator stays loading/checking or shows degraded state
    expect(await screen.findByText('The Auralis FastAPI backend is currently unreachable.')).toBeInTheDocument();

    // Main navigation remains interactive
    const settingsLink = screen.getAllByRole('link', { name: /settings/i })[0];
    expect(settingsLink).toBeInTheDocument();
  });

  it('WORKFLOW 6: WebSocket disconnect -> UI remains stable -> reconnect attempted -> synchronization resumes', async () => {
    render(<App />);

    // Simulate connection offline state
    act(() => {
      (syncService as any).wsClient.stateListeners.forEach((listener: any) => listener('RECONNECTING'));
    });
    expect(useVoiceStore.getState().connectionState).toBe('RECONNECTING');

    // Re-establish connection and verify synchronization handles websocket events
    act(() => {
      (syncService as any).wsClient.stateListeners.forEach((listener: any) => listener('CONNECTED'));
      (syncService as any).handleSyncMessage({
        type: 'LISTENER_STATUS_CHANGED',
        payload: { running: true }
      });
    });

    expect(useVoiceStore.getState().connectionState).toBe('CONNECTED');
    expect(useVoiceStore.getState().listenerRunning).toBe(true);
  });

  it('WORKFLOW 7: Component error -> Local ErrorBoundary catches it -> AppLayout remains functional', async () => {
    shouldDashboardCrash = true;
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<App />);

    // Local error boundary catches the exception and renders fallback UI
    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();

    // Top application shell components are preserved and remain functional
    expect(screen.getByText('Voice File Manager')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /dashboard/i })[0]).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});
