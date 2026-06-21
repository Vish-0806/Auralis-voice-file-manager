import React from 'react';
import { 
  File, FileText, FileImage, FileAudio, FileVideo, 
  Folder, FolderArchive, FileCode, ExternalLink, Trash2,
  FolderOpen
} from 'lucide-react';

export default function SearchResults({ results, onOpenAction, onDeleteAction }) {
  const getFileIcon = (type, name = '') => {
    const ext = (type || '').toLowerCase();
    
    // Check folders
    if (!ext || ext === 'directory' || ext === 'folder') {
      return <Folder className="file-icon text-amber" size={20} />;
    }
    
    // Check popular document extensions
    if (ext === '.pdf') {
      return <FileText className="file-icon text-rose" size={20} />;
    }
    if (['.txt', '.doc', '.docx', '.md', '.rtf'].includes(ext)) {
      return <FileText className="file-icon text-blue" size={20} />;
    }
    
    // Check images
    if (['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.bmp'].includes(ext)) {
      return <FileImage className="file-icon text-emerald" size={20} />;
    }
    
    // Check audio
    if (['.mp3', '.wav', '.flac', '.ogg', '.m4a'].includes(ext)) {
      return <FileAudio className="file-icon text-cyan" size={20} />;
    }
    
    // Check videos
    if (['.mp4', '.mkv', '.avi', '.mov', '.wmv'].includes(ext)) {
      return <FileVideo className="file-icon text-violet" size={20} />;
    }
    
    // Check archives
    if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(ext)) {
      return <FolderArchive className="file-icon text-yellow" size={20} />;
    }
    
    // Check programming code
    if (['.js', '.jsx', '.ts', '.tsx', '.py', '.html', '.css', '.json', '.c', '.cpp', '.java'].includes(ext)) {
      return <FileCode className="file-icon text-violet" size={20} />;
    }
    
    // Fallback file icon
    return <File className="file-icon text-muted" size={20} />;
  };

  if (!results || results.length === 0) {
    return null;
  }

  return (
    <div className="search-results-wrapper">
      <div className="results-count-header">
        <span>SEARCH MATCHES ({results.length})</span>
      </div>
      <div className="results-grid">
        {results.map((item, idx) => {
          const isDir = !item.type || item.type === 'directory';
          
          return (
            <div key={idx} className="result-card glass-panel fade-in-up" style={{ animationDelay: `${idx * 0.05}s` }}>
              <div className="result-main">
                {getFileIcon(item.type, item.name)}
                <div className="result-info">
                  <div className="result-name" title={item.name}>{item.name}</div>
                  <div className="result-path" title={item.path}>{item.path}</div>
                </div>
              </div>
              
              <div className="result-actions">
                <button 
                  onClick={() => onOpenAction(item.name)}
                  className="btn-card-action btn-action-open"
                  title={`Open ${item.name}`}
                >
                  <FolderOpen size={14} /> Open
                </button>
                <button 
                  onClick={() => onDeleteAction(item.name)}
                  className="btn-card-action btn-action-delete"
                  title={`Delete ${item.name}`}
                >
                  <Trash2 size={14} /> Delete
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <style>{`
        .search-results-wrapper {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          width: 100%;
        }

        .results-count-header {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-muted);
          letter-spacing: 0.05em;
        }

        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1rem;
        }

        .result-card {
          padding: 0.85rem 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          justify-content: space-between;
          border-left: 3px solid transparent;
        }

        .result-card:hover {
          transform: translateY(-2px);
          border-left-color: var(--accent-violet);
          background: var(--glass-bg-hover);
        }

        .result-main {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          overflow: hidden;
        }

        .file-icon {
          flex-shrink: 0;
        }

        .text-rose { color: var(--accent-rose); }
        .text-blue { color: #3b82f6; }
        .text-emerald { color: var(--accent-emerald); }
        .text-cyan { color: var(--accent-cyan); }
        .text-violet { color: var(--accent-violet); }
        .text-amber { color: var(--accent-amber); }
        .text-yellow { color: #eab308; }
        .text-muted { color: var(--text-muted); }

        .result-info {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
          overflow: hidden;
          width: 100%;
        }

        .result-name {
          font-size: 0.9rem;
          font-weight: 600;
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .result-path {
          font-size: 0.75rem;
          color: var(--text-muted);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          font-family: monospace;
        }

        .result-actions {
          display: flex;
          gap: 0.5rem;
          border-top: 1px solid var(--glass-border);
          padding-top: 0.6rem;
        }

        .btn-card-action {
          flex: 1;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--glass-border);
          color: var(--text-secondary);
          padding: 0.3rem 0.5rem;
          border-radius: var(--radius-sm);
          font-size: 0.75rem;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.3rem;
          transition: var(--transition-smooth);
        }

        .btn-action-open:hover {
          background: rgba(6, 182, 212, 0.1);
          color: var(--accent-cyan);
          border-color: rgba(6, 182, 212, 0.3);
        }

        .btn-action-delete:hover {
          background: rgba(244, 63, 94, 0.1);
          color: var(--accent-rose);
          border-color: rgba(244, 63, 94, 0.3);
        }

        /* Fade-in animation */
        .fade-in-up {
          opacity: 0;
          transform: translateY(10px);
          animation: card-fade-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes card-fade-in {
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
