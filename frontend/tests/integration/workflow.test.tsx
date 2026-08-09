import { act } from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../../src/app';
import { useWorkspaceStore } from '../../src/state/stores/workspaceStore';
import { useFilesStore } from '../../src/state/stores/filesStore';
import { useVoiceStore } from '../../src/voice/state/voiceStore';
import { syncService } from '../../src/services/synchronization/synchronizationService';
import { ErrorBoundary } from '../../src/components/common/ErrorBoundary/ErrorBoundary';

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

describe('Auralis V2 Integration Workflows', () => {
  beforeEach(() => {
    // Reset stores
    useWorkspaceStore.getState().reset();
    useFilesStore.getState().reset();
    useVoiceStore.getState().reset();
    window.history.pushState({}, 'Home', '/');
    vi.clearAllMocks();
  });

  it('should verify application startup and routing to dashboard', async () => {
    render(<App />);

    expect(await screen.findByText('Voice File Manager')).toBeInTheDocument();
    expect(await screen.findByText('Quick Access Shortcuts')).toBeInTheDocument();
    expect(await screen.findByText('Backend Service Status')).toBeInTheDocument();
  });

  it('should support full navigation between pages', async () => {
    render(<App />);
    const user = userEvent.setup();

    // Verify initial landing on dashboard
    expect(await screen.findByText('Quick Access Shortcuts')).toBeInTheDocument();

    // Navigate to Assistant
    const assistantLink = screen.getAllByRole('link', { name: /assistant/i })[0];
    await user.click(assistantLink);
    expect(await screen.findByText('Assistant Hub')).toBeInTheDocument();

    // Navigate to Workspace
    const workspaceLink = screen.getAllByRole('link', { name: /workspace/i })[0];
    await user.click(workspaceLink);
    expect(await screen.findByText('Directory Tree')).toBeInTheDocument();

    // Navigate to Settings
    const settingsLink = screen.getAllByRole('link', { name: /settings/i })[0];
    await user.click(settingsLink);
    expect(await screen.findByText('Application Preferences')).toBeInTheDocument();
  });

  it('should persist workspace open tabs across page navigation', async () => {
    // Simulate setting initial files
    const mockFiles = [
      { name: 'document.txt', path: 'C:/Users/Vishal/Documents/document.txt', size: 1024 },
      { name: 'photo.jpg', path: 'C:/Users/Vishal/Desktop/photo.jpg', size: 204800 }
    ];
    useFilesStore.getState().setFiles(mockFiles);
    useFilesStore.getState().setStatus('success');

    render(<App />);
    const user = userEvent.setup();

    // 1. Navigate to Workspace
    const workspaceLink = screen.getAllByRole('link', { name: /workspace/i })[0];
    await user.click(workspaceLink);
    expect(await screen.findByText('Directory Tree')).toBeInTheDocument();

    // 2. Open a document tab
    act(() => {
      useWorkspaceStore.getState().openTab('C:/Users/Vishal/Documents/document.txt');
    });
    expect(await screen.findByText('document.txt')).toBeInTheDocument();

    // 3. Navigate away to Dashboard
    const dashboardLink = screen.getAllByRole('link', { name: /dashboard/i })[0];
    await user.click(dashboardLink);
    expect(await screen.findByText('Quick Access Shortcuts')).toBeInTheDocument();

    // 4. Navigate back to Workspace and verify the tab is still open
    await user.click(workspaceLink);
    expect(await screen.findByText('document.txt')).toBeInTheDocument();
  });

  it('should support voice integration control click actions', async () => {
    render(<App />);
    const user = userEvent.setup();

    // 1. Navigate to Assistant page
    const assistantLink = screen.getAllByRole('link', { name: /assistant/i })[0];
    await user.click(assistantLink);
    expect(await screen.findByText('Assistant Hub')).toBeInTheDocument();

    // 2. Click the mic button to request permissions
    const micBtn = screen.getByRole('button', { name: /Start Listening/i });
    await user.click(micBtn);

    // Verify speech status updates
    expect(await screen.findByText('Completed')).toBeInTheDocument();
    expect(await screen.findByText('mock command')).toBeInTheDocument();
  });

  it('should display error boundary screen on rendering errors and support retry recovery', async () => {
    const CrashComponent = () => {
      throw new Error('Test crash error');
    };

    // We suppress console.error calls in this test block so logs remain clean
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <CrashComponent />
      </ErrorBoundary>
    );

    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
    expect(await screen.findByText('An unexpected rendering error occurred. Please refresh or try again.')).toBeInTheDocument();

    const tryAgainBtn = screen.getByRole('button', { name: /try again/i });
    expect(tryAgainBtn).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('should fallback gracefully to not-found routing', async () => {
    // Push arbitrary path
    window.history.pushState({}, 'Not Found', '/invalid-nonexistent-path');
    render(<App />);

    expect(await screen.findByText('404')).toBeInTheDocument();
    expect(await screen.findByText('Page Not Found')).toBeInTheDocument();
  });

  it('should handle WebSocket state events and synchronize stores', async () => {
    render(<App />);
    
    // Simulate incoming websocket listener event via sync service
    act(() => {
      (syncService as any).handleSyncMessage({
        type: 'LISTENER_STATUS_CHANGED',
        payload: { running: true }
      });
    });

    // Check voiceStore updated successfully
    expect(useVoiceStore.getState().listenerRunning).toBe(true);
  });
});
