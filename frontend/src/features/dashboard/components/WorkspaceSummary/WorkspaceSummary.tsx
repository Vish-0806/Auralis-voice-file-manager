import React from 'react';
import { 
  useWorkspaceStore, 
  useFilesStore,
  selectOpenTabs,
  selectActiveTab,
  selectCurrentDirectory,
  selectSelectedFileCount
} from '../../../../state';
import { Card } from '../../../../components/common';

export const WorkspaceSummary: React.FC = () => {
  const openTabs = useWorkspaceStore(selectOpenTabs) || [];
  const activeTab = useWorkspaceStore(selectActiveTab);
  const currentDirectory = useFilesStore(selectCurrentDirectory);
  const selectedCount = useFilesStore(selectSelectedFileCount);

  return (
    <Card className="border-0 shadow-sm mb-4 h-100">
      <Card.Header>
        <h6 className="mb-0 text-secondary fw-bold d-flex align-items-center gap-2">
          <i className="bi bi-briefcase text-primary" aria-hidden="true"></i>
          <span>Workspace Stats</span>
        </h6>
      </Card.Header>
      
      <Card.Body>
        <div className="d-flex flex-column gap-3.5" style={{ minHeight: '120px' }}>
          <div className="row g-2 text-center">
            <div className="col-6">
              <div className="bg-light p-2.5 rounded-3 border">
                <span className="text-muted d-block small mb-0.5">Open Tabs</span>
                <strong className="fs-5 text-dark" data-testid="open-tabs-count">{openTabs.length}</strong>
              </div>
            </div>
            <div className="col-6">
              <div className="bg-light p-2.5 rounded-3 border">
                <span className="text-muted d-block small mb-0.5">Selected Files</span>
                <strong className="fs-5 text-dark" data-testid="selected-files-count">{selectedCount}</strong>
              </div>
            </div>
          </div>

          <div className="d-flex flex-column gap-2" style={{ fontSize: '0.85rem' }}>
            <div className="d-flex align-items-center justify-content-between p-2 rounded-2 hover-bg-light">
              <span className="text-muted">Active Directory:</span>
              <span className="fw-semibold text-secondary text-truncate ms-2" style={{ maxWidth: '180px' }} title={currentDirectory}>
                {currentDirectory}
              </span>
            </div>

            <div className="d-flex align-items-center justify-content-between p-2 rounded-2 hover-bg-light">
              <span className="text-muted">Focused Document:</span>
              <span className="fw-semibold text-secondary text-truncate ms-2" style={{ maxWidth: '180px' }} title={activeTab || 'None'}>
                {activeTab ? activeTab.split('/').pop() : 'None'}
              </span>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};
export default WorkspaceSummary;
