import React from 'react';
import { FileSystemNode } from '../../utils/virtualFS';

interface FileListProps {
  nodes: FileSystemNode[];
  selectedIds: string[];
  onSelect: (node: FileSystemNode) => void;
  onOpen: (node: FileSystemNode) => void;
}

export const FileList: React.FC<FileListProps> = ({
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
    if (bytes === undefined) return '-';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return '-';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '-';
    }
  };

  return (
    <div className="table-responsive p-3">
      <table className="table table-hover align-middle mb-0" style={{ fontSize: '0.85rem' }}>
        <thead>
          <tr className="table-light">
            <th style={{ width: '40px' }} aria-label="Selection Box"></th>
            <th>Name</th>
            <th>Size</th>
            <th>Type</th>
            <th>Date Modified</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((node) => {
            const isSelected = selectedIds.includes(node.path);
            
            return (
              <tr
                key={node.path}
                onClick={() => onSelect(node)}
                onDoubleClick={() => onOpen(node)}
                className={isSelected ? 'table-primary' : ''}
                style={{ cursor: 'pointer' }}
                data-testid={`file-list-row-${node.name}`}
              >
                <td>
                  {!node.is_directory && (
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="form-check-input"
                      style={{ pointerEvents: 'none' }}
                      aria-label={`Select ${node.name}`}
                    />
                  )}
                </td>
                <td>
                  <div className="d-flex align-items-center gap-2">
                    <i className={`bi ${getFileIcon(node)} fs-5`} aria-hidden="true" />
                    <span className="fw-medium text-dark">{node.name}</span>
                  </div>
                </td>
                <td>{node.is_directory ? '-' : formatSize(node.size)}</td>
                <td>{node.is_directory ? 'Folder' : (node.type || 'Unknown').toUpperCase()}</td>
                <td>{node.is_directory ? '-' : formatDate(node.modified)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
export default FileList;
