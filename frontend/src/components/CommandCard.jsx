import React from 'react';
import { 
  FolderPlus, Trash2, Move, Copy, Search, Eye, 
  CheckCircle2, XCircle, AlertTriangle, HelpCircle,
  MessageSquare, Keyboard, Mic
} from 'lucide-react';

export default function CommandCard({ item }) {
  const {
    timestamp,
    type,
    command,
    outcome,
    action,
    target,
    destination,
    summaryMessage,
  } = item;

  const formattedTime = new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  const getActionIcon = () => {
    switch (action) {
      case 'create_folder':
        return <FolderPlus size={14} />;
      case 'delete':
        return <Trash2 size={14} />;
      case 'move':
        return <Move size={14} />;
      case 'copy':
        return <Copy size={14} />;
      case 'search':
        return <Search size={14} />;
      case 'open':
        return <Eye size={14} />;
      case 'confirm':
      case 'cancel':
        return <CheckCircle2 size={14} />;
      default:
        return <HelpCircle size={14} />;
    }
  };

  const getOutcomeDetails = () => {
    switch (outcome) {
      case 'success':
        return {
          icon: <CheckCircle2 size={16} className="text-emerald" />,
          className: 'outcome-success',
        };
      case 'error':
        return {
          icon: <XCircle size={16} className="text-rose" />,
          className: 'outcome-error',
        };
      case 'pending_confirmation':
        return {
          icon: <AlertTriangle size={16} className="text-amber" />,
          className: 'outcome-pending',
        };
      case 'ignored':
        return {
          icon: <HelpCircle size={16} className="text-muted" />,
          className: 'outcome-ignored',
        };
      default:
        return {
          icon: <CheckCircle2 size={16} className="text-muted" />,
          className: '',
        };
    }
  };

  const outcomeDetails = getOutcomeDetails();

  return (
    <div className={`command-card-item glass-panel ${outcomeDetails.className}`}>
      <div className="card-top-row">
        <div className="command-source-time">
          {type === 'voice' ? (
            <Mic size={14} className="source-icon-voice" title="Voice command" />
          ) : (
            <Keyboard size={14} className="source-icon-text" title="Typed command" />
          )}
          <span className="command-time">{formattedTime}</span>
        </div>
        
        <span className={`action-pill pill-${action}`}>
          {getActionIcon()}
          {action.replace('_', ' ')}
        </span>
      </div>

      <div className="command-text">
        "{command}"
      </div>

      {(target || destination) && (
        <div className="command-entities">
          {target && (
            <span className="entity-item">
              <span className="entity-label">Target:</span>
              <span className="entity-value">{target}</span>
            </span>
          )}
          {destination && (
            <span className="entity-item">
              <span className="entity-label">To:</span>
              <span className="entity-value">{destination}</span>
            </span>
          )}
        </div>
      )}

      <div className="command-outcome">
        {outcomeDetails.icon}
        <span className="outcome-msg">{summaryMessage}</span>
      </div>

      <style>{`
        .command-card-item {
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.65rem;
          border-left: 3px solid rgba(255, 255, 255, 0.1);
        }

        .command-card-item.outcome-success {
          border-left-color: var(--accent-emerald);
        }

        .command-card-item.outcome-error {
          border-left-color: var(--accent-rose);
        }

        .command-card-item.outcome-pending {
          border-left-color: var(--accent-amber);
        }

        .command-card-item.outcome-ignored {
          border-left-color: var(--text-muted);
          opacity: 0.8;
        }

        .card-top-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .command-source-time {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .source-icon-voice {
          color: var(--accent-rose);
        }

        .source-icon-text {
          color: var(--accent-cyan);
        }

        .action-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.2rem 0.5rem;
          border-radius: var(--radius-sm);
          font-size: 0.7rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.03em;
        }

        .pill-create_folder {
          background: rgba(16, 185, 129, 0.12);
          color: var(--accent-emerald);
          border: 1px solid rgba(16, 185, 129, 0.2);
        }

        .pill-delete {
          background: rgba(244, 63, 94, 0.12);
          color: var(--accent-rose);
          border: 1px solid rgba(244, 63, 94, 0.2);
        }

        .pill-move {
          background: rgba(139, 92, 246, 0.12);
          color: var(--accent-violet);
          border: 1px solid rgba(139, 92, 246, 0.2);
        }

        .pill-copy {
          background: rgba(6, 182, 212, 0.12);
          color: var(--accent-cyan);
          border: 1px solid rgba(6, 182, 212, 0.2);
        }

        .pill-search {
          background: rgba(245, 158, 11, 0.12);
          color: var(--accent-amber);
          border: 1px solid rgba(245, 158, 11, 0.2);
        }

        .pill-open {
          background: rgba(20, 184, 166, 0.12);
          color: #14b8a6;
          border: 1px solid rgba(20, 184, 166, 0.2);
        }

        .pill-confirm, .pill-cancel {
          background: rgba(255, 255, 255, 0.06);
          color: var(--text-secondary);
          border: 1px solid var(--glass-border);
        }

        .command-text {
          font-size: 0.95rem;
          font-weight: 500;
          color: var(--text-primary);
          font-style: italic;
        }

        .command-entities {
          display: flex;
          flex-wrap: wrap;
          gap: 0.75rem;
          font-size: 0.8rem;
          background: rgba(0, 0, 0, 0.15);
          padding: 0.4rem 0.6rem;
          border-radius: var(--radius-sm);
        }

        .entity-item {
          display: flex;
          gap: 0.25rem;
        }

        .entity-label {
          color: var(--text-muted);
          font-weight: 600;
        }

        .entity-value {
          color: var(--text-primary);
          font-family: monospace;
          background: rgba(255, 255, 255, 0.05);
          padding: 0.05rem 0.25rem;
          border-radius: 4px;
        }

        .command-outcome {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.85rem;
          margin-top: 0.25rem;
        }

        .text-emerald { color: var(--accent-emerald); }
        .text-rose { color: var(--accent-rose); }
        .text-amber { color: var(--accent-amber); }
        .text-muted { color: var(--text-muted); }
        
        .outcome-msg {
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
}
