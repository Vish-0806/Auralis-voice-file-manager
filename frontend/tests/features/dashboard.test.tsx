import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../../src/pages/dashboard/DashboardPage';
import { assistantService } from '../../src/services/api/assistantService';
import { useFilesStore, useWorkspaceStore } from '../../src/state';
import { LayoutContext } from '../../src/layouts/AppLayout';

// Mock the assistantService API client calls
vi.mock('../../src/services/api/assistantService', () => {
  return {
    assistantService: {
      getHealth: vi.fn(),
      getStatus: vi.fn()
    }
  };
});

const mockLayoutContext = {
  isMobileOpen: false,
  setMobileOpen: vi.fn(),
  isCollapsed: false,
  setCollapsed: vi.fn(),
  actions: null,
  setActions: vi.fn(),
  description: null,
  setDescription: vi.fn(),
};

describe('Dashboard Feature Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useFilesStore.getState().reset();
    useWorkspaceStore.getState().reset();
  });

  it('renders Dashboard Page components and checks header', async () => {
    // Mock healthy service responses
    vi.mocked(assistantService.getHealth).mockResolvedValue({
      status: 'ok',
      version: '2.0.0',
      timestamp: '2026-08-09T10:00:00Z'
    });
    vi.mocked(assistantService.getStatus).mockResolvedValue({
      platform: {
        system: 'Windows',
        release: '11',
        version: '10.0.22000',
        machine: 'AMD64',
        python_version: '3.11.2'
      },
      loaded_capabilities: ['files', 'listener', 'voice'],
      assistant_status: 'ready'
    });

    render(
      <MemoryRouter>
        <LayoutContext.Provider value={mockLayoutContext}>
          <DashboardPage />
        </LayoutContext.Provider>
      </MemoryRouter>
    );

    // Header greeting text
    expect(screen.getByText(/User/)).toBeInTheDocument();
    
    // Quick Actions links
    expect(screen.getByText('Open Assistant')).toBeInTheDocument();
    expect(screen.getByText('Workspace')).toBeInTheDocument();
    expect(screen.getByText('File Manager')).toBeInTheDocument();

    // Verify online badge renders
    await waitFor(() => {
      expect(screen.getByTestId('backend-status-badge')).toHaveTextContent('Online');
    });

    // Check system platform info rendering
    expect(screen.getByText(/Windows/)).toBeInTheDocument();
    expect(screen.getByText(/3 active modules/)).toBeInTheDocument();
  });

  it('renders degraded status when platform status check fails', async () => {
    vi.mocked(assistantService.getHealth).mockResolvedValue({
      status: 'ok',
      version: '2.0.0',
      timestamp: '2026-08-09T10:00:00Z'
    });
    vi.mocked(assistantService.getStatus).mockRejectedValue(new Error('Status unavailable'));

    render(
      <MemoryRouter>
        <LayoutContext.Provider value={mockLayoutContext}>
          <DashboardPage />
        </LayoutContext.Provider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('backend-status-badge')).toHaveTextContent('Degraded');
    });
  });

  it('renders offline status when backend connection fails', async () => {
    vi.mocked(assistantService.getHealth).mockRejectedValue(new Error('Network error'));

    render(
      <MemoryRouter>
        <LayoutContext.Provider value={mockLayoutContext}>
          <DashboardPage />
        </LayoutContext.Provider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('backend-status-badge')).toHaveTextContent('System Offline');
    });
  });

  it('renders empty recent files and workspace stats', () => {
    render(
      <MemoryRouter>
        <LayoutContext.Provider value={mockLayoutContext}>
          <DashboardPage />
        </LayoutContext.Provider>
      </MemoryRouter>
    );

    // Empty message
    expect(screen.getByText('No recently loaded files found.')).toBeInTheDocument();

    // Workspace stats counters
    expect(screen.getByTestId('open-tabs-count')).toHaveTextContent('0');
    expect(screen.getByTestId('selected-files-count')).toHaveTextContent('0');
    expect(screen.getByText('Focused Document:')).toBeInTheDocument();
  });

  it('renders populated recent files list and supports click redirection', () => {
    // Populate store files
    const mockFiles = [
      { name: 'report.pdf', path: 'C:/Users/Vishal/Documents/report.pdf', size: 10240, modified: '2026-08-09T10:00:00Z' },
      { name: 'notes.txt', path: 'C:/Users/Vishal/Desktop/notes.txt', size: 512, modified: '2026-08-09T10:00:00Z' }
    ];
    useFilesStore.getState().setFiles(mockFiles);
    useFilesStore.getState().setStatus('success');

    render(
      <MemoryRouter>
        <LayoutContext.Provider value={mockLayoutContext}>
          <DashboardPage />
        </LayoutContext.Provider>
      </MemoryRouter>
    );

    expect(screen.getByText('report.pdf')).toBeInTheDocument();
    expect(screen.getByText('notes.txt')).toBeInTheDocument();

    // Clicking a recent file triggers openTab
    const recentBtn = screen.getByText('report.pdf');
    fireEvent.click(recentBtn);

    expect(useWorkspaceStore.getState().openTabs).toContain('C:/Users/Vishal/Documents/report.pdf');
    expect(useWorkspaceStore.getState().activeTab).toBe('C:/Users/Vishal/Documents/report.pdf');
  });

  it('renders empty recent activity logs', () => {
    render(
      <MemoryRouter>
        <LayoutContext.Provider value={mockLayoutContext}>
          <DashboardPage />
        </LayoutContext.Provider>
      </MemoryRouter>
    );

    expect(screen.getByText('No Recent Activity')).toBeInTheDocument();
    expect(screen.getByText(/Log activity will appear/)).toBeInTheDocument();
  });
});
