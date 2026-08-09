import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useFilesStore, selectFilesList, selectFilesStatus, selectFilesError } from '../../../../state';
import { useWorkspaceStore } from '../../../../state/stores/workspaceStore';
import { Card, Spinner } from '../../../../components/common';

export const RecentFiles: React.FC = () => {
  const files = useFilesStore(selectFilesList) || [];
  const status = useFilesStore(selectFilesStatus);
  const error = useFilesStore(selectFilesError);
  
  const openTab = useWorkspaceStore((state) => state.openTab);
  const navigate = useNavigate();

  const handleFileClick = (filePath: string) => {
    openTab(filePath);
    navigate('/workspace');
  };

  const recentList = files.slice(0, 5);

  return (
    <Card className="border-0 shadow-sm mb-4 h-100">
      <Card.Header>
        <h6 className="mb-0 text-secondary fw-bold d-flex align-items-center gap-2">
          <i className="bi bi-clock-history text-primary" aria-hidden="true"></i>
          <span>Recent Files</span>
        </h6>
      </Card.Header>
      
      <Card.Body className="recent-files-content" style={{ minHeight: '120px' }}>
        {status === 'loading' && (
          <div className="d-flex align-items-center justify-content-center py-5">
            <Spinner size="sm" variant="primary" className="me-2" />
            <span className="text-muted small">Loading files...</span>
          </div>
        )}

        {status === 'error' && error && (
          <div className="alert alert-danger small p-2 mb-0" role="alert">
            <i className="bi bi-exclamation-circle-fill me-1"></i>
            {error}
          </div>
        )}

        {status !== 'loading' && status !== 'error' && recentList.length === 0 && (
          <div className="text-center py-4 text-muted">
            <i className="bi bi-folder-symlink fs-3 d-block mb-1.5 text-gray-300"></i>
            <span className="small d-block">No recently loaded files found.</span>
            <span className="small text-muted" style={{ fontSize: '0.75rem' }}>
              Search for files in the File Manager to populate this list.
            </span>
          </div>
        )}

        {status !== 'loading' && status !== 'error' && recentList.length > 0 && (
          <div className="list-group list-group-flush gap-1">
            {recentList.map((file) => {
              // Get file extension icon
              let icon = 'bi-file-earmark';
              const ext = file.name.split('.').pop()?.toLowerCase();
              if (['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext || '')) icon = 'bi-file-earmark-image';
              if (['txt', 'md', 'json', 'csv'].includes(ext || '')) icon = 'bi-file-earmark-text';

              return (
                <button
                  key={file.path}
                  type="button"
                  onClick={() => handleFileClick(file.path)}
                  className="list-group-item list-group-item-action border-0 rounded-3 d-flex align-items-center justify-content-between p-2.5 text-start hover-bg-light"
                >
                  <div className="d-flex align-items-center gap-2.5 overflow-hidden">
                    <i className={`bi ${icon} text-primary fs-5 flex-shrink-0`} aria-hidden="true"></i>
                    <div className="overflow-hidden">
                      <strong className="d-block text-dark small text-truncate mb-0.5">{file.name}</strong>
                      <span className="text-muted text-truncate d-block" style={{ fontSize: '0.7rem' }}>
                        {file.path}
                      </span>
                    </div>
                  </div>
                  <i className="bi bi-chevron-right text-muted flex-shrink-0 ms-2" style={{ fontSize: '0.8rem' }} />
                </button>
              );
            })}
          </div>
        )}
      </Card.Body>
    </Card>
  );
};
export default RecentFiles;
