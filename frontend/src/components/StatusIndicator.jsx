import React from 'react';
import { Mic, Activity, AlertCircle, Play, Square } from 'lucide-react';

export default function StatusIndicator({ status, listenerActive, toggleListener }) {
  const getStatusConfig = () => {
    switch (status) {
      case 'listening':
        return {
          color: 'var(--accent-rose)',
          glow: 'var(--accent-rose-glow)',
          label: 'Auralis is listening...',
          icon: <Mic className="status-icon pulsate" size={18} style={{ color: 'var(--accent-rose)' }} />,
        };
      case 'processing':
        return {
          color: 'var(--accent-amber)',
          glow: 'var(--accent-amber-glow)',
          label: 'Analyzing audio...',
          icon: <Activity className="status-icon spin" size={18} style={{ color: 'var(--accent-amber)' }} />,
        };
      case 'error':
        return {
          color: 'var(--accent-rose)',
          glow: 'var(--accent-rose-glow)',
          label: 'Error occurred',
          icon: <AlertCircle className="status-icon" size={18} style={{ color: 'var(--accent-rose)' }} />,
        };
      case 'success':
        return {
          color: 'var(--accent-emerald)',
          glow: 'var(--accent-emerald-glow)',
          label: 'Command executed',
          icon: <Activity className="status-icon" size={18} style={{ color: 'var(--accent-emerald)' }} />,
        };
      case 'idle':
      default:
        return {
          color: 'var(--accent-violet)',
          glow: 'var(--accent-violet-glow)',
          label: 'Auralis is ready',
          icon: <Mic className="status-icon" size={18} style={{ color: 'var(--text-secondary)' }} />,
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className="status-indicator-container glass-panel">
      <div className="status-indicator-header">
        <span className="status-badge-title">SYSTEM STATUS</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span 
            className="status-dot" 
            style={{ 
              backgroundColor: config.color, 
              boxShadow: `0 0 10px 2px ${config.glow}`
            }} 
          />
          <span className="status-label">{config.label}</span>
        </div>
      </div>

      <div className="status-indicator-details">
        <div className="status-detail-row">
          <div className="status-detail-info">
            <span className="detail-label">Background Listener</span>
            <span className={`status-badge ${listenerActive ? 'active' : 'inactive'}`}>
              {listenerActive ? 'Active' : 'Offline'}
            </span>
          </div>
          <button 
            onClick={toggleListener}
            className={`btn-listener-toggle ${listenerActive ? 'active' : ''}`}
            title={listenerActive ? 'Stop continuous listener' : 'Start continuous listener'}
          >
            {listenerActive ? (
              <>
                <Square size={14} fill="currentColor" /> Stop
              </>
            ) : (
              <>
                <Play size={14} fill="currentColor" /> Start
              </>
            )}
          </button>
        </div>
        <p className="status-helper-text">
          {listenerActive 
            ? 'Continuous mode is active. Say "Hey Auralis" followed by a command to manage files.' 
            : 'Continuous listening is disabled. Use the microphone button or type below.'}
        </p>
      </div>

      <style>{`
        .status-indicator-container {
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .status-indicator-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--glass-border);
          padding-bottom: 0.75rem;
        }

        .status-badge-title {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-muted);
          letter-spacing: 0.05em;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
          transition: var(--transition-smooth);
        }

        .status-label {
          font-size: 0.85rem;
          font-weight: 500;
          color: var(--text-primary);
        }

        .status-indicator-details {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .status-detail-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 1rem;
        }

        .status-detail-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .detail-label {
          font-size: 0.8rem;
          color: var(--text-secondary);
        }

        .btn-listener-toggle {
          background: rgba(255, 255, 255, 0.06);
          border: 1px solid var(--glass-border);
          color: var(--text-primary);
          padding: 0.4rem 0.8rem;
          border-radius: var(--radius-sm);
          font-size: 0.8rem;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 0.35rem;
          transition: var(--transition-smooth);
        }

        .btn-listener-toggle:hover {
          background: rgba(255, 255, 255, 0.12);
          border-color: rgba(255, 255, 255, 0.2);
        }

        .btn-listener-toggle.active {
          background: rgba(244, 63, 94, 0.15);
          color: var(--accent-rose);
          border-color: rgba(244, 63, 94, 0.3);
        }

        .btn-listener-toggle.active:hover {
          background: rgba(244, 63, 94, 0.25);
        }

        .status-helper-text {
          font-size: 0.75rem;
          color: var(--text-muted);
          line-height: 1.4;
          margin-top: 0.25rem;
        }

        .pulsate {
          animation: status-pulsate 1.5s ease-in-out infinite;
        }

        @keyframes status-pulsate {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
