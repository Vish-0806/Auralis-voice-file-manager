import React from 'react';
import { Card } from '../../../../components/common';

interface FilePreviewProps {
  filePath: string | null;
  fileName: string | null;
  className?: string;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  filePath,
  fileName,
  className = ''
}) => {
  if (!filePath || !fileName) {
    return (
      <Card className={`file-preview-card border-0 shadow-sm ${className}`}>
        <Card.Body className="d-flex align-items-center justify-content-center text-center py-5 text-muted">
          <div>
            <i className="bi bi-file-earmark-lock2 fs-2 mb-2 d-block text-gray-300"></i>
            <span className="small">Select a file to show its preview staging.</span>
          </div>
        </Card.Body>
      </Card>
    );
  }

  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  const isImage = ['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext);
  const isText = ['txt', 'md', 'json', 'csv', 'ts', 'js', 'html', 'css'].includes(ext);

  // Premium mock data generation for preview presentation
  const getMockTextContent = (name: string, extension: string) => {
    if (extension === 'csv') {
      return `Date,Transaction,Amount,Category,Status\n2026-08-01,Stripe Payout,$1200.00,Revenue,Cleared\n2026-08-03,AWS Cloud Server,-$342.10,Hosting,Cleared\n2026-08-05,Google Workspace,-$36.00,Software,Cleared\n2026-08-09,FastAPI Server Host,-$120.00,Hosting,Staged`;
    }
    if (extension === 'md') {
      return `# Auralis Documentation\n\nStaged file: **${name}**\n\n- File Buffer: Validated\n- Voice Control Status: Listening\n- Last Synchronized: Just now\n\nUse Voice Assistant commands to move or organize this buffer.`;
    }
    if (extension === 'json') {
      return `{\n  "documentName": "${name}",\n  "fileSize": 45102,\n  "status": "staged",\n  "systemCheck": "passed",\n  "tags": ["financial", "invoice", "august"]\n}`;
    }
    return `System Log Buffer - Staged File [${name}]\n-----------------------------------------------\n[INFO] 10:24:05 - Connection established to Auralis websocket.\n[INFO] 10:24:06 - Staged file: ${filePath}\n[WARNING] 10:24:10 - Local mic permission approved.\n[SUCCESS] 10:24:12 - Voice activity command processed successfully.\n\n-- Staged file contents validated --`;
  };

  return (
    <Card className={`file-preview-card border-0 shadow-sm ${className}`}>
      <Card.Header>
        <div className="d-flex align-items-center gap-2 w-100">
          <i className="bi bi-eye text-primary" aria-hidden="true"></i>
          <span className="text-truncate fw-semibold text-secondary small" title={fileName}>
            Staging Preview: {fileName}
          </span>
        </div>
      </Card.Header>
      
      <Card.Body>
        <div className="preview-container d-flex flex-column gap-3">
          {isImage && (
            <div className="text-center bg-light p-3 rounded-3 border border-dashed">
              {/* Visual preview for images */}
              <div className="d-inline-block bg-white p-2 rounded-2 shadow-sm mb-2 border">
                <i className="bi bi-image text-info" style={{ fontSize: '3.5rem' }} aria-hidden="true" />
              </div>
              <strong className="d-block small text-dark mb-1">{fileName}</strong>
              <span className="text-muted d-block" style={{ fontSize: '0.75rem' }}>
                Image resolution and metadata parsed locally.
              </span>
            </div>
          )}

          {isText && (
            <div className="bg-dark text-light p-3 rounded-3 font-monospace border" style={{ fontSize: '0.8rem', maxHeight: '200px', overflowY: 'auto' }}>
              <pre className="mb-0 text-start" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {getMockTextContent(fileName, ext)}
              </pre>
            </div>
          )}

          {!isImage && !isText && (
            <div className="text-center py-4 bg-light rounded-3 border">
              <i className="bi bi-file-earmark-binary fs-2 text-muted mb-2 d-block"></i>
              <span className="small d-block text-secondary fw-semibold mb-1">Binary Preview Unavailable</span>
              <span className="small text-muted px-3 d-block" style={{ fontSize: '0.75rem' }}>
                Direct rendering of binary type (.{(ext || 'bin').toUpperCase()}) is not supported. Use external commands to inspect.
              </span>
            </div>
          )}

          <div className="bg-light p-2.5 rounded-3 border" style={{ fontSize: '0.8rem' }}>
            <div className="d-flex align-items-baseline gap-2 mb-1.5">
              <span className="text-muted text-nowrap" style={{ width: '80px' }}>Full Path:</span>
              <span className="text-dark font-monospace text-break text-start">{filePath}</span>
            </div>
            <div className="d-flex align-items-baseline gap-2">
              <span className="text-muted text-nowrap" style={{ width: '80px' }}>Type:</span>
              <span className="badge bg-secondary-subtle text-secondary border">{ext.toUpperCase() || 'UNKNOWN'} File</span>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};
export default FilePreview;
