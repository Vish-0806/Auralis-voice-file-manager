import React from 'react';
import { 
  useFilesStore, 
  useWorkspaceStore,
  selectFilesList,
  selectCurrentDirectory,
  selectFileSortMode,
  selectFileSortDirection,
  selectFileViewMode,
  selectSelectedFileIds
} from '../../../../state';
import { getVirtualNodes, FileSystemNode } from '../../utils/virtualFS';
import { FileToolbar } from '../FileToolbar/FileToolbar';
import { FileGrid } from '../FileGrid/FileGrid';
import { FileList } from '../FileList/FileList';
import { Card, EmptyState } from '../../../../components/common';

export const FileBrowser: React.FC = () => {
  const files = useFilesStore(selectFilesList) || [];
  const currentDirectory = useFilesStore(selectCurrentDirectory);
  const sortMode = useFilesStore(selectFileSortMode);
  const sortDirection = useFilesStore(selectFileSortDirection);
  const viewMode = useFilesStore(selectFileViewMode);
  const selectedFileIds = useFilesStore(selectSelectedFileIds) || [];
  const status = useFilesStore((state) => state.status);
  
  const setCurrentDirectory = useFilesStore((state) => state.setCurrentDirectory);
  const toggleFileSelection = useFilesStore((state) => state.toggleFileSelection);
  const openTab = useWorkspaceStore((state) => state.openTab);

  // 1. Resolve virtual folders and files in current directory
  const nodes = getVirtualNodes(files, currentDirectory);

  // 2. Sort nodes: Folders first, then apply sort criteria
  const sortedNodes = [...nodes].sort((a, b) => {
    if (a.is_directory && !b.is_directory) return -1;
    if (!a.is_directory && b.is_directory) return 1;

    let comparison = 0;
    if (sortMode === 'name') {
      comparison = a.name.localeCompare(b.name);
    } else if (sortMode === 'size') {
      const sizeA = a.size || 0;
      const sizeB = b.size || 0;
      comparison = sizeA - sizeB;
    } else if (sortMode === 'date') {
      const dateA = a.modified ? new Date(a.modified).getTime() : 0;
      const dateB = b.modified ? new Date(b.modified).getTime() : 0;
      comparison = dateA - dateB;
    }

    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const handleSelect = (node: FileSystemNode) => {
    if (node.is_directory) return;
    toggleFileSelection(node.path);
  };

  const handleOpen = (node: FileSystemNode) => {
    if (node.is_directory) {
      setCurrentDirectory(node.path);
    } else {
      openTab(node.path);
    }
  };

  return (
    <Card className="file-browser border-0 shadow-sm overflow-hidden p-0 h-100">
      <FileToolbar />
      
      <div 
        className="file-browser-list-container bg-light" 
        style={{ minHeight: '320px', maxHeight: '500px', overflowY: 'auto' }}
      >
        {status === 'loading' && sortedNodes.length === 0 && (
          <div className="d-flex flex-column align-items-center justify-content-center py-5 text-muted">
            <div className="spinner-border spinner-border-sm text-primary mb-2" role="status" />
            <span className="small">Fetching document indices...</span>
          </div>
        )}

        {sortedNodes.length === 0 && status !== 'loading' && (
          <div className="d-flex align-items-center justify-content-center py-5">
            <EmptyState
              title="No Files Found"
              description="No staged files found in this directory. Try refining your search query in the search bar above."
              icon="bi-folder2-open text-muted"
            />
          </div>
        )}

        {sortedNodes.length > 0 && (
          viewMode === 'grid' ? (
            <FileGrid
              nodes={sortedNodes}
              selectedIds={selectedFileIds}
              onSelect={handleSelect}
              onOpen={handleOpen}
            />
          ) : (
            <FileList
              nodes={sortedNodes}
              selectedIds={selectedFileIds}
              onSelect={handleSelect}
              onOpen={handleOpen}
            />
          )
        )}
      </div>
    </Card>
  );
};
export default FileBrowser;
