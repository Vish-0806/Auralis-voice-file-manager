import React from 'react';
import { useWorkspaceStore, selectOpenTabs, selectActiveTab } from '../../../../state';

export const WorkspaceTabs: React.FC = () => {
  const openTabs = useWorkspaceStore(selectOpenTabs) || [];
  const activeTab = useWorkspaceStore(selectActiveTab);
  const setActiveTab = useWorkspaceStore((state) => state.setActiveTab);
  const closeTab = useWorkspaceStore((state) => state.closeTab);

  if (openTabs.length === 0) return null;

  return (
    <div 
      className="workspace-tabs-container bg-light border-bottom px-3 py-2 d-flex align-items-center gap-2 overflow-x-auto"
      style={{ whiteSpace: 'nowrap', minHeight: '48px' }}
      role="tablist"
      aria-label="Workspace document tabs"
    >
      {openTabs.map((tab) => {
        const isSelected = activeTab === tab;
        const fileName = tab.split('/').pop() || tab.split('\\').pop() || '';
        
        return (
          <div
            key={tab}
            className={`d-inline-flex align-items-center gap-2 px-3 py-1.5 border rounded-pill shadow-sm transition-all text-decoration-none ${
              isSelected 
                ? 'bg-white border-primary text-primary fw-semibold' 
                : 'bg-white-50 border-light text-secondary hover-bg-white'
            }`}
            style={{ cursor: 'pointer', fontSize: '0.8rem' }}
            onClick={() => setActiveTab(tab)}
            role="tab"
            aria-selected={isSelected}
            aria-controls="workspace-tabpanel"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter') setActiveTab(tab);
            }}
            data-testid={`workspace-tab-${fileName}`}
          >
            <i className="bi bi-file-earmark-code" aria-hidden="true"></i>
            <span className="text-truncate" style={{ maxWidth: '120px' }}>{fileName}</span>
            <button
              type="button"
              className="btn-close"
              style={{ width: '8px', height: '8px', padding: '0' }}
              aria-label={`Close ${fileName} tab`}
              onClick={(e) => {
                e.stopPropagation();
                closeTab(tab);
              }}
            />
          </div>
        );
      })}
    </div>
  );
};
export default WorkspaceTabs;
