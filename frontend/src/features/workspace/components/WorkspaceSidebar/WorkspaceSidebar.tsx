import React from 'react';
import { useFilesStore, selectCurrentDirectory, selectFilesList } from '../../../../state';

export const WorkspaceSidebar: React.FC = () => {
  const currentDirectory = useFilesStore(selectCurrentDirectory);
  const setCurrentDirectory = useFilesStore((state) => state.setCurrentDirectory);
  const files = useFilesStore(selectFilesList) || [];

  // Extract all unique virtual directory paths
  const directoriesSet = new Set<string>(['/', '/Desktop', '/Documents', '/Downloads']);
  
  files.forEach((file) => {
    const normalized = file.path.replace(/\\/g, '/');
    const match = normalized.match(/\/(Desktop|Documents|Downloads)(\/.*)?$/i);
    if (match) {
      const rootDir = match[1];
      const subPath = match[2] || '';
      const parts = subPath.split('/').filter(Boolean);
      let cumulativePath = '/' + rootDir;
      parts.slice(0, -1).forEach((part) => {
        cumulativePath += '/' + part;
        directoriesSet.add(cumulativePath);
      });
    }
  });

  const dirs = Array.from(directoriesSet).sort((a, b) => a.localeCompare(b));

  const handleDirectoryClick = (dirPath: string) => {
    setCurrentDirectory(dirPath);
  };

  return (
    <div className="workspace-sidebar bg-white border-end h-100 p-3" style={{ minWidth: '220px' }}>
      <h6 className="text-secondary small fw-bold text-uppercase mb-3 d-flex align-items-center gap-2">
        <i className="bi bi-folder-fill text-warning"></i>
        <span>Directory Tree</span>
      </h6>
      
      <div className="list-group list-group-flush gap-1">
        {dirs.map((dir) => {
          const depth = dir.split('/').filter(Boolean).length;
          const isSelected = currentDirectory === dir;
          const folderName = dir === '/' ? 'Home' : dir.split('/').pop() || '';
          
          return (
            <button
              key={dir}
              type="button"
              onClick={() => handleDirectoryClick(dir)}
              className={`list-group-item list-group-item-action border-0 rounded-2 p-2 text-start d-flex align-items-center gap-2 small ${
                isSelected ? 'bg-primary-subtle text-primary fw-semibold' : 'text-secondary'
              }`}
              style={{ paddingLeft: `${Math.max(8, depth * 12)}px` }}
              data-testid={`sidebar-dir-${dir}`}
            >
              <i className={`bi ${dir === '/' ? 'bi-house' : isSelected ? 'bi-folder2-open text-primary' : 'bi-folder text-warning'}`}></i>
              <span className="text-truncate">{folderName}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
export default WorkspaceSidebar;
