import React, { useEffect } from 'react';
import { 
  useWorkspaceStore, 
  useFilesStore,
  selectOpenPanels, 
  selectActiveTab,
  selectSelectedFileIds
} from '../../../../state';
import { WorkspaceSidebar } from '../WorkspaceSidebar/WorkspaceSidebar';
import { WorkspaceTabs } from '../WorkspaceTabs/WorkspaceTabs';
import { FileBrowser } from '../FileBrowser/FileBrowser';
import { FilePreview } from '../FilePreview/FilePreview';
import { IconButton } from '../../../../components/common';

export const WorkspaceShell: React.FC = () => {
  const openPanels = useWorkspaceStore(selectOpenPanels) || [];
  const togglePanel = useWorkspaceStore((state) => state.togglePanel);
  const setOpenPanels = useWorkspaceStore((state) => state.setOpenPanels);
  const activeTab = useWorkspaceStore(selectActiveTab);
  const selectedFileIds = useFilesStore(selectSelectedFileIds) || [];
  const currentDirectory = useFilesStore((state) => state.currentDirectory);

  const isSidebarOpen = openPanels.includes('sidebar');
  const isPreviewOpen = openPanels.includes('preview');

  // Initialize panels on mount if empty
  useEffect(() => {
    if (openPanels.length === 0) {
      setOpenPanels(['sidebar', 'preview']);
    }
  }, [openPanels.length, setOpenPanels]);

  // Determine what file to preview: active tab takes precedence, fallback to first selected file
  const previewPath = activeTab || (selectedFileIds.length > 0 ? selectedFileIds[0] : null);
  const previewName = previewPath ? previewPath.split('/').pop() || '' : null;

  return (
    <div className="workspace-shell d-flex flex-column gap-3">
      {/* Workspace Panel Controllers */}
      <div className="d-flex align-items-center justify-content-between bg-white border rounded-3 p-2 px-3 shadow-sm">
        <div className="d-flex align-items-center gap-2">
          <IconButton
            icon={isSidebarOpen ? 'bi-layout-sidebar-inset-reverse text-primary' : 'bi-layout-sidebar-inset'}
            aria-label="Toggle Directory Sidebar"
            onClick={() => togglePanel('sidebar')}
            tooltip="Toggle Directory Sidebar"
            size="sm"
          />
          <span className="small text-muted font-monospace">Path: {currentDirectory}</span>
        </div>

        <div className="d-flex align-items-center gap-2">
          <IconButton
            icon={isPreviewOpen ? 'bi-layout-sidebar-reverse text-primary' : 'bi-layout-sidebar'}
            aria-label="Toggle Preview Panel"
            onClick={() => togglePanel('preview')}
            tooltip="Toggle Preview Panel"
            size="sm"
          />
        </div>
      </div>

      {/* Main Workspace Layout Grid */}
      <div className="row g-3">
        {/* Left Sidebar */}
        {isSidebarOpen && (
          <div className="col-12 col-lg-3 d-none d-lg-block">
            <WorkspaceSidebar />
          </div>
        )}

        {/* Central File Browser / Tab Panel */}
        <div className={`col-12 ${
          isSidebarOpen && isPreviewOpen 
            ? 'col-lg-6' 
            : isSidebarOpen || isPreviewOpen 
              ? 'col-lg-9' 
              : 'col-lg-12'
        }`}>
          <div className="d-flex flex-column gap-2.5 h-100">
            <WorkspaceTabs />
            
            {/* If tab is active, display preview directly, otherwise show File Browser */}
            {activeTab ? (
              <div className="card border-0 shadow-sm p-0 position-relative">
                <div className="position-absolute top-0 end-0 p-2.5 z-3">
                  <button 
                    type="button" 
                    className="btn btn-sm btn-outline-secondary" 
                    onClick={() => useWorkspaceStore.getState().setActiveTab(null)}
                    aria-label="Back to File Browser"
                  >
                    <i className="bi bi-arrow-left me-1"></i>
                    Back to Browser
                  </button>
                </div>
                <FilePreview filePath={activeTab} fileName={activeTab.split('/').pop() || ''} />
              </div>
            ) : (
              <FileBrowser />
            )}
          </div>
        </div>

        {/* Right Collapsible Preview Panel */}
        {isPreviewOpen && (
          <div className="col-12 col-lg-3">
            <FilePreview filePath={previewPath} fileName={previewName} />
          </div>
        )}
      </div>
    </div>
  );
};
export default WorkspaceShell;
