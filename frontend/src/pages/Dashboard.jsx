import React, { useState } from 'react';
import { useVoiceCommands } from '../hooks/useVoiceCommands';
import VoiceButton from '../components/VoiceButton';
import StatusIndicator from '../components/StatusIndicator';
import CommandCard from '../components/CommandCard';
import SearchResults from '../components/SearchResults';
import { 
  Keyboard, Send, RefreshCw, Trash2, HelpCircle, 
  Info, AlertOctagon, Check, X, FileSearch, ShieldAlert 
} from 'lucide-react';

export default function Dashboard() {
  const {
    listenerActive,
    status,
    lastMessage,
    pendingAction,
    searchResults,
    history,
    triggerVoiceListen,
    submitTextCommand,
    respondToConfirmation,
    toggleContinuousListener,
    clearHistory,
    clearSearchResults,
  } = useVoiceCommands();

  const [textCommand, setTextCommand] = useState('');

  const handleSubmitText = (e) => {
    e.preventDefault();
    if (!textCommand.trim()) return;
    submitTextCommand(textCommand);
    setTextCommand('');
  };

  const handleOpenResult = (name) => {
    submitTextCommand(`open ${name}`);
  };

  const handleDeleteResult = (name) => {
    submitTextCommand(`delete ${name}`);
  };

  return (
    <div className="app-container">
      {/* Top Banner Header */}
      <header className="app-header">
        <div className="app-title-container">
          <div className="app-logo-mark">🎙️</div>
          <div>
            <h1 className="app-title-logo">Auralis</h1>
            <span className="app-subtitle">Voice-Enabled Intelligent File Operations</span>
          </div>
        </div>
        <div className="header-status-badge">
          <span className="engine-label">VOICE ENGINE</span>
          <span className={`status-badge ${status === 'listening' ? 'active' : 'inactive'}`} style={{
            backgroundColor: status === 'listening' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(255, 255, 255, 0.05)',
            borderColor: status === 'listening' ? 'var(--accent-rose)' : 'var(--glass-border)',
            color: status === 'listening' ? 'var(--accent-rose)' : 'var(--text-secondary)'
          }}>
            {status.toUpperCase()}
          </span>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <main className="dashboard-grid">
        
        {/* Left Side: Inputs and Voice Controls */}
        <section className="control-panel">
          
          {/* Glowing Voice Button Card */}
          <VoiceButton 
            status={status} 
            onClick={triggerVoiceListen} 
          />
          
          {/* Status Indicator Panel */}
          <StatusIndicator 
            status={status}
            listenerActive={listenerActive}
            toggleListener={toggleContinuousListener}
          />

          {/* Interactive User Confirmation Dialogue */}
          {pendingAction && (
            <div className="confirmation-panel glass-panel pulse-border-amber">
              <div className="confirmation-header">
                <ShieldAlert className="text-amber" size={20} />
                <span>CONFIRMATION REQUIRED</span>
              </div>
              <div className="confirmation-body">
                <p className="confirmation-message">{pendingAction.message}</p>
                <div className="confirmation-details">
                  <span className="detail-tag">Action: {pendingAction.rawAction?.action}</span>
                  <span className="detail-tag">Target: {pendingAction.rawAction?.target}</span>
                </div>
              </div>
              <div className="confirmation-footer">
                <button 
                  onClick={() => respondToConfirmation(false)}
                  className="btn-confirm btn-cancel-confirm"
                >
                  <X size={14} /> Cancel (No)
                </button>
                <button 
                  onClick={() => respondToConfirmation(true)}
                  className="btn-confirm btn-agree-confirm"
                >
                  <Check size={14} /> Confirm (Yes)
                </button>
              </div>
            </div>
          )}

          {/* Fallback Text Console */}
          <div className="text-console-card glass-panel">
            <div className="panel-header">
              <h2 className="panel-title"><Keyboard size={16} /> Keyboard Command</h2>
            </div>
            <form onSubmit={handleSubmitText} className="text-input-form">
              <div className="text-input-wrapper">
                <input
                  type="text"
                  value={textCommand}
                  onChange={(e) => setTextCommand(e.target.value)}
                  placeholder="Type a command (e.g., find report.pdf)..."
                  className="text-input"
                  disabled={status === 'processing' || status === 'listening'}
                />
                <Keyboard className="text-input-icon" size={16} />
              </div>
              <button 
                type="submit" 
                className="btn-send-command"
                disabled={!textCommand.trim() || status === 'processing' || status === 'listening'}
                title="Send Command"
              >
                <Send size={14} />
              </button>
            </form>
            <div className="command-tips">
              <span className="tips-title">Supported Commands:</span>
              <ul className="tips-list">
                <li><code>find &lt;filename&gt;</code> - Scan folders recursively</li>
                <li><code>create folder &lt;name&gt; in documents</code> - Add locations</li>
                <li><code>move &lt;file&gt; to downloads</code> - Move files safely</li>
                <li><code>delete &lt;filename&gt;</code> - Delete with protection</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Right Side: Log Feed and Search Output */}
        <section className="main-content-panel">
          
          {/* Notification Banner */}
          <div className="notification-banner glass-panel">
            <div className="notification-icon">
              {status === 'error' ? (
                <AlertOctagon className="text-rose" size={20} />
              ) : (
                <Info className="text-cyan" size={20} />
              )}
            </div>
            <div className="notification-content">
              <div className="notification-title">SYSTEM NOTIFICATION</div>
              <div className="notification-body-text">{lastMessage}</div>
            </div>
            {searchResults.length > 0 && (
              <button 
                onClick={clearSearchResults}
                className="btn-clear-search"
                title="Clear search results"
              >
                <FileSearch size={14} /> Clear Search
              </button>
            )}
          </div>

          {/* Search Result Grid */}
          <SearchResults 
            results={searchResults} 
            onOpenAction={handleOpenResult}
            onDeleteAction={handleDeleteResult}
          />

          {/* Action Log / Command History List */}
          <div className="history-log-panel glass-panel">
            <div className="panel-header">
              <h2 className="panel-title">⏱️ Command Activity Log</h2>
              {history.length > 0 && (
                <button 
                  onClick={clearHistory}
                  className="btn-clear-logs"
                  title="Clear history logs"
                >
                  <Trash2 size={12} /> Clear Logs
                </button>
              )}
            </div>
            
            <div className="history-list">
              {history.length === 0 ? (
                <div className="empty-history">
                  <HelpCircle size={36} className="text-muted" />
                  <p>No activity recorded yet.</p>
                  <span>Spoken or typed commands will be logged here.</span>
                </div>
              ) : (
                history.map((item) => (
                  <CommandCard key={item.id} item={item} />
                ))
              )}
            </div>
          </div>
        </section>

      </main>

      <style>{`
        .header-status-badge {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .engine-label {
          font-size: 0.65rem;
          font-weight: 700;
          color: var(--text-muted);
          letter-spacing: 0.05em;
        }

        /* Confirmation Dialog Box */
        .confirmation-panel {
          padding: 1.25rem;
          border-left: 4px solid var(--accent-amber);
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .pulse-border-amber {
          box-shadow: 0 0 16px 2px rgba(245, 158, 11, 0.2);
          animation: border-amber-glow 2s infinite;
        }

        @keyframes border-amber-glow {
          0%, 100% { border-color: rgba(245, 158, 11, 0.3); }
          50% { border-color: rgba(245, 158, 11, 0.6); }
        }

        .confirmation-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.75rem;
          font-weight: 800;
          color: var(--accent-amber);
          letter-spacing: 0.05em;
        }

        .confirmation-message {
          font-size: 0.95rem;
          font-weight: 500;
          color: var(--text-primary);
        }

        .confirmation-details {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }

        .detail-tag {
          font-size: 0.7rem;
          background: rgba(0, 0, 0, 0.2);
          padding: 0.2rem 0.5rem;
          border-radius: var(--radius-sm);
          color: var(--text-secondary);
        }

        .confirmation-footer {
          display: flex;
          gap: 0.75rem;
        }

        .btn-confirm {
          flex: 1;
          padding: 0.5rem;
          border-radius: var(--radius-sm);
          font-weight: 600;
          font-size: 0.8rem;
          cursor: pointer;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.35rem;
          transition: var(--transition-smooth);
        }

        .btn-cancel-confirm {
          background: rgba(244, 63, 94, 0.15);
          color: var(--accent-rose);
          border: 1px solid rgba(244, 63, 94, 0.3);
        }

        .btn-cancel-confirm:hover {
          background: rgba(244, 63, 94, 0.25);
        }

        .btn-agree-confirm {
          background: rgba(16, 185, 129, 0.15);
          color: var(--accent-emerald);
          border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .btn-agree-confirm:hover {
          background: rgba(16, 185, 129, 0.25);
        }

        /* Text console styles */
        .text-console-card {
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .text-input-form {
          display: flex;
          gap: 0.5rem;
        }

        .btn-send-command {
          background: var(--accent-violet);
          color: white;
          border: none;
          width: 44px;
          height: 42px;
          border-radius: var(--radius-md);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: var(--transition-smooth);
          box-shadow: 0 4px 10px 0 var(--accent-violet-glow);
        }

        .btn-send-command:hover:not(:disabled) {
          background: #7c3aed;
          transform: translateY(-1px);
        }

        .btn-send-command:disabled {
          background: rgba(255, 255, 255, 0.05);
          color: var(--text-muted);
          box-shadow: none;
          cursor: not-allowed;
        }

        .command-tips {
          background: rgba(0, 0, 0, 0.12);
          padding: 0.75rem;
          border-radius: var(--radius-sm);
          font-size: 0.75rem;
        }

        .tips-title {
          font-weight: 700;
          color: var(--text-secondary);
          margin-bottom: 0.35rem;
          display: block;
        }

        .tips-list {
          list-style-type: none;
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
          color: var(--text-muted);
        }

        .tips-list code {
          color: var(--accent-cyan);
          background: rgba(255, 255, 255, 0.03);
          padding: 0.05rem 0.2rem;
          border-radius: 3px;
        }

        /* Notifications */
        .notification-banner {
          padding: 1rem 1.25rem;
          display: flex;
          align-items: center;
          gap: 1rem;
          border-left: 3px solid var(--accent-cyan);
          box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
        }

        .notification-icon {
          flex-shrink: 0;
        }

        .notification-content {
          flex-grow: 1;
        }

        .notification-title {
          font-size: 0.7rem;
          font-weight: 700;
          color: var(--text-muted);
          letter-spacing: 0.05em;
        }

        .notification-body-text {
          font-size: 0.9rem;
          color: var(--text-primary);
          font-weight: 500;
          margin-top: 0.1rem;
        }

        .btn-clear-search {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--glass-border);
          color: var(--text-secondary);
          padding: 0.35rem 0.7rem;
          border-radius: var(--radius-sm);
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 0.35rem;
          transition: var(--transition-smooth);
        }

        .btn-clear-search:hover {
          background: rgba(255, 255, 255, 0.1);
          color: var(--text-primary);
        }

        /* History log */
        .history-log-panel {
          padding: 1.25rem;
          flex-grow: 1;
          display: flex;
          flex-direction: column;
          gap: 1rem;
          min-height: 350px;
        }

        .btn-clear-logs {
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.75rem;
          font-weight: 600;
          transition: var(--transition-smooth);
        }

        .btn-clear-logs:hover {
          color: var(--accent-rose);
        }

        .history-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          max-height: 480px;
          overflow-y: auto;
          padding-right: 0.25rem;
        }

        .empty-history {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          color: var(--text-muted);
          padding: 3rem 0;
          text-align: center;
        }

        .empty-history p {
          font-size: 0.95rem;
          font-weight: 600;
          margin-top: 0.5rem;
          color: var(--text-secondary);
        }

        .empty-history span {
          font-size: 0.8rem;
        }
      `}</style>
    </div>
  );
}
