import React from 'react';
import { FileSystemNode } from '../../utils/virtualFS';

interface FileGridProps {
  nodes: FileSystemNode[];
  selectedIds: string[];
  onSelect: (node: FileSystemNode) => void;
  onOpen: (node: FileSystemNode) => void;
}

export const FileGrid: React.FC<FileGridProps> = ({
  nodes,
  selectedIds,
  onSelect,
  onOpen
}) => {
  const getFileIcon = (node: FileSystemNode) => {
    if (node.is_directory) return 'bi-folder-fill text-warning';
    
    const ext = node.name.split('.').pop()?.toLowerCase();
    if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext || '')) return 'bi-file-earmark-image text-info';
    if (['txt', 'md', 'json', 'csv'].includes(ext || '')) return 'bi-file-earmark-text text-primary';
    return 'bi-file-earmark text-secondary';
  };

  const formatSize = (bytes?: number) => {
    if (bytes === undefined) return '';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="row g-3 p-3">
      {nodes.map((node) => {
        const isSelected = selectedIds.includes(node.path);
        
        return (
          <div key={node.path} className="col-6 col-sm-4 col-md-3 col-xl-2">
            <div
              className={`card h-100 border p-2 text-center clickable transition-all position-relative ${
                isSelected ? 'border-primary bg-primary-subtle shadow-sm' : 'hover-bg-light'
              }`}
              style={{ cursor: 'pointer', minHeight: '110px' }}
              onClick={() => onSelect(node)}
              onDoubleClick={() => onOpen(node)}
              role="checkbox"
              aria-checked={isSelected}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onSelect(node);
                if (e.key === ' ') {
                  e.preventDefault();
                  onSelect(node);
                }
              }}
              data-testid={`file-grid-item-${node.name}`}
            >
              {/* Checkbox selector for file nodes */}
              {!node.is_directory && (
                <div 
                  className="position-absolute top-0 start-0 p-1.5"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelect(node);
                  }}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}}
                    className="form-check-input m-0"
                    style={{ pointerEvents: 'none', width: '13px', height: '13px' }}
                    aria-label={`Select ${node.name}`}
                  />
                </div>
              )}

              <div className="my-2.5">
                <i className={`bi ${getFileIcon(node)}`} style={{ fontSize: '2rem' }} aria-hidden="true" />
              </div>
              
              <div className="w-100 px-1 overflow-hidden">
                <span className="d-block text-dark small text-truncate fw-semibold mb-0.5" title={node.name}>
                  {node.name}
                </span>
                {!node.is_directory && node.size !== undefined && (
                  <span className="text-muted text-truncate d-block" style={{ fontSize: '0.7rem' }}>
                    {formatSize(node.size)}
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
export default FileGrid;
