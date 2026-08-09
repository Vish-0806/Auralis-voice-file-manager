import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { WorkspacePage } from '../../src/pages/workspace/WorkspacePage';
import { FilesPage } from '../../src/pages/files/FilesPage';
import { useFilesStore, useWorkspaceStore } from '../../src/state';
import { getVirtualNodes } from '../../src/features/workspace/utils/virtualFS';
import { LayoutContext } from '../../src/layouts/AppLayout';

// Mock files search service
vi.mock('../../src/services/api/filesService', () => {
  return {
    filesService: {
      searchFiles: vi.fn().mockResolvedValue([
        { name: 'document.txt', path: 'C:/Users/Vishal/Documents/document.txt', size: 1024, modified: '2026-08-09T10:00:00Z' },
        { name: 'photo.jpg', path: 'C:/Users/Vishal/Desktop/photo.jpg', size: 204800, modified: '2026-08-09T10:00:00Z' },
        { name: 'data.csv', path: 'C:/Users/Vishal/Documents/Staging/data.csv', size: 500, modified: '2026-08-09T10:00:00Z' }
      ])
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

describe('Workspace & File Browser Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useFilesStore.getState().reset();
    useWorkspaceStore.getState().reset();
  });

  describe('Virtual FS Node Mapper Helper', () => {
    const mockFilesList = [
      { name: 'a.txt', path: 'C:/Users/Vishal/Documents/a.txt' },
      { name: 'b.png', path: 'C:/Users/Vishal/Desktop/b.png' },
      { name: 'c.csv', path: 'C:/Users/Vishal/Documents/Project/c.csv' }
    ];

    it('resolves root level folder nodes Desktop, Documents, Downloads', () => {
      const nodes = getVirtualNodes(mockFilesList, '/');
      const folders = nodes.filter(n => n.is_directory).map(n => n.name);
      expect(folders).toContain('Desktop');
      expect(folders).toContain('Documents');
      expect(folders).toContain('Downloads');
    });

    it('resolves files directly inside virtual directory Documents', () => {
      const nodes = getVirtualNodes(mockFilesList, '/Documents');
      const files = nodes.filter(n => !n.is_directory).map(n => n.name);
      const dirs = nodes.filter(n => n.is_directory).map(n => n.name);
      
      expect(files).toContain('a.txt');
      expect(dirs).toContain('Project');
    });

    it('resolves files inside subfolder Project', () => {
      const nodes = getVirtualNodes(mockFilesList, '/Documents/Project');
      const files = nodes.filter(n => !n.is_directory).map(n => n.name);
      expect(files).toContain('c.csv');
    });
  });

  describe('WorkspaceShell View panels', () => {
    it('renders Workspace Page showing Shell and panel layouts', () => {
      const mockFiles = [
        { name: 'document.txt', path: 'C:/Users/Vishal/Documents/document.txt', size: 1024 },
        { name: 'photo.jpg', path: 'C:/Users/Vishal/Desktop/photo.jpg', size: 204800 }
      ];
      useFilesStore.getState().setFiles(mockFiles);
      useFilesStore.getState().setStatus('success');
      useWorkspaceStore.getState().setOpenPanels(['sidebar', 'preview']);

      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <WorkspacePage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      // Verify directory structure elements exist
      expect(screen.getByText('Directory Tree')).toBeInTheDocument();
      expect(screen.getAllByText('Home')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Desktop')[0]).toBeInTheDocument();

      // Check collapsible panel buttons
      expect(screen.getByRole('button', { name: /Toggle Directory Sidebar/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Toggle Preview Panel/i })).toBeInTheDocument();
    });

    it('toggles directory sidebar visibility when button clicked', () => {
      useWorkspaceStore.getState().setOpenPanels(['sidebar', 'preview']);

      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <WorkspacePage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      const toggleSidebarBtn = screen.getByRole('button', { name: /Toggle Directory Sidebar/i });
      fireEvent.click(toggleSidebarBtn);

      // Verify that sidebar panel collapses / store state is updated
      expect(useWorkspaceStore.getState().openPanels).not.toContain('sidebar');
    });
  });

  describe('FileBrowser & View Controls', () => {
    beforeEach(() => {
      const mockFiles = [
        { name: 'document.txt', path: 'C:/Users/Vishal/Documents/document.txt', size: 1024, modified: '2026-08-09T10:00:00Z' },
        { name: 'photo.jpg', path: 'C:/Users/Vishal/Desktop/photo.jpg', size: 204800, modified: '2026-08-09T10:00:00Z' }
      ];
      useFilesStore.getState().setFiles(mockFiles);
      useFilesStore.getState().setStatus('success');
      useFilesStore.getState().setCurrentDirectory('/Documents');
    });

    it('should switch between List and Grid modes', () => {
      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <FilesPage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      // Renders as grid initially
      expect(screen.getByTestId('file-grid-item-document.txt')).toBeInTheDocument();

      // Switch to List View
      const listViewBtn = screen.getByRole('button', { name: /List View/i });
      fireEvent.click(listViewBtn);

      // Grid item is replaced by list row
      expect(screen.getByTestId('file-list-row-document.txt')).toBeInTheDocument();
    });

    it('should toggle selection when checkbox is clicked', () => {
      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <FilesPage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      const checkbox = screen.getByLabelText('Select document.txt');
      expect(checkbox).not.toBeChecked();

      fireEvent.click(checkbox);
      expect(useFilesStore.getState().selectedFileIds).toContain('C:/Users/Vishal/Documents/document.txt');
    });

    it('opens file tab when item double-clicked', () => {
      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <FilesPage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      const fileItem = screen.getByTestId('file-grid-item-document.txt');
      fireEvent.doubleClick(fileItem);

      expect(useWorkspaceStore.getState().openTabs).toContain('C:/Users/Vishal/Documents/document.txt');
      expect(useWorkspaceStore.getState().activeTab).toBe('C:/Users/Vishal/Documents/document.txt');
    });
  });

  describe('File Preview Component', () => {
    it('shows empty text selection when no preview file is focused', () => {
      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <WorkspacePage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      expect(screen.getByText('Select a file to show its preview staging.')).toBeInTheDocument();
    });

    it('renders image details preview', () => {
      useWorkspaceStore.getState().openTab('C:/Users/Vishal/Desktop/photo.jpg');

      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <WorkspacePage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      expect(screen.getAllByText('Staging Preview: photo.jpg')[0]).toBeInTheDocument();
      expect(screen.getAllByText('Image resolution and metadata parsed locally.')[0]).toBeInTheDocument();
    });

    it('renders text file content preview', () => {
      useWorkspaceStore.getState().openTab('C:/Users/Vishal/Documents/document.txt');

      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <WorkspacePage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      expect(screen.getAllByText('Staging Preview: document.txt')[0]).toBeInTheDocument();
      // Verifies matching mock content block
      expect(screen.getAllByText(/System Log Buffer/)[0]).toBeInTheDocument();
    });

    it('closes workspace tab when close button is clicked', () => {
      useWorkspaceStore.getState().openTab('C:/Users/Vishal/Documents/document.txt');
      useWorkspaceStore.getState().openTab('C:/Users/Vishal/Desktop/photo.jpg');

      render(
        <MemoryRouter>
          <LayoutContext.Provider value={mockLayoutContext}>
            <WorkspacePage />
          </LayoutContext.Provider>
        </MemoryRouter>
      );

      expect(screen.getByTestId('workspace-tab-photo.jpg')).toBeInTheDocument();
      
      const closeBtn = screen.getByLabelText('Close photo.jpg tab');
      fireEvent.click(closeBtn);

      expect(useWorkspaceStore.getState().openTabs).not.toContain('C:/Users/Vishal/Desktop/photo.jpg');
    });
  });
});
