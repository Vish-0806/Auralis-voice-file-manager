import React from 'react';
import { Link } from 'react-router-dom';

interface ActionItem {
  label: string;
  desc: string;
  path: string;
  icon: string;
  colorClass: string;
}

const ACTIONS: ActionItem[] = [
  {
    label: 'Open Assistant',
    desc: 'Chat with natural language conversational helper.',
    path: '/assistant',
    icon: 'bi-chat-left-dots-fill',
    colorClass: 'text-primary bg-primary-subtle'
  },
  {
    label: 'Workspace',
    desc: 'Stage documents and edit workspace file buffers.',
    path: '/workspace',
    icon: 'bi-kanban-fill',
    colorClass: 'text-success bg-success-subtle'
  },
  {
    label: 'File Manager',
    desc: 'Browse, manage, and recursively search files.',
    path: '/files',
    icon: 'bi-folder-fill',
    colorClass: 'text-warning bg-warning-subtle'
  },
  {
    label: 'Settings',
    desc: 'Configure application density and accessibility settings.',
    path: '/settings',
    icon: 'bi-gear-fill',
    colorClass: 'text-secondary bg-secondary-subtle'
  }
];

export const QuickActions: React.FC = () => {
  return (
    <div className="card border-0 shadow-sm p-4 mb-4">
      <h6 className="card-title text-secondary mb-3 fw-bold d-flex align-items-center gap-2">
        <i className="bi bi-grid-fill text-primary" aria-hidden="true"></i>
        <span>Quick Access Shortcuts</span>
      </h6>
      <div className="row g-3">
        {ACTIONS.map((act) => (
          <div key={act.path} className="col-12 col-md-6">
            <Link 
              to={act.path} 
              className="d-flex align-items-start gap-3 p-3 border rounded-3 text-decoration-none text-secondary hover-bg-light transition-all h-100"
            >
              <div className={`p-2.5 rounded-3 ${act.colorClass} d-flex align-items-center justify-content-center`}>
                <i className={`bi ${act.icon} fs-5`}></i>
              </div>
              <div>
                <strong className="d-block text-dark small fw-bold mb-0.5">{act.label}</strong>
                <span className="text-muted small" style={{ fontSize: '0.75rem', lineHeight: '1.2' }}>{act.desc}</span>
              </div>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
};
export default QuickActions;
