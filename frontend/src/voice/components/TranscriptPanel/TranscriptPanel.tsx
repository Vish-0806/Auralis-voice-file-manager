import React from 'react';
import { Card } from '../../../components/common';
import { TranscriptPanelProps } from './TranscriptPanel.types';

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  partialTranscript = '',
  finalTranscript = '',
  latestResult = null,
  processing = false,
  error = null,
  className = ''
}) => {
  const hasContent = partialTranscript || finalTranscript || latestResult;

  return (
    <Card className={`transcript-panel shadow-sm border-0 ${className}`}>
      <Card.Header>
        <h6 className="mb-0 text-secondary d-flex align-items-center gap-2">
          <i className="bi bi-justify-left text-primary" aria-hidden="true"></i>
          <span>Live Transcription</span>
        </h6>
      </Card.Header>
      <Card.Body>
        <div className="transcript-content position-relative" style={{ minHeight: '100px' }}>
          {!hasContent && !processing && (
            <div className="text-center text-muted py-4">
              <i className="bi bi-mic fs-2 d-block mb-2 text-gray-300" aria-hidden="true"></i>
              <span className="small">Start speaking to see the transcript...</span>
            </div>
          )}

          {processing && !hasContent && (
            <div className="d-flex flex-column align-items-center justify-content-center py-4 text-info">
              <div className="spinner-border spinner-border-sm mb-2" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <span className="small">Processing speech input...</span>
            </div>
          )}

          {error && (
            <div className="text-danger small mb-3">
              <i className="bi bi-exclamation-circle me-1" aria-hidden="true"></i>
              {error}
            </div>
          )}

          {/* Display Transcripts */}
          {(finalTranscript || partialTranscript) && (
            <div className="mb-3">
              <p className="mb-0 lh-base" style={{ fontSize: '0.95rem' }}>
                {finalTranscript && (
                  <span className="final-transcript text-dark fw-medium">
                    {finalTranscript}{' '}
                  </span>
                )}
                {partialTranscript && (
                  <span className="partial-transcript text-muted fst-italic">
                    {partialTranscript}...
                  </span>
                )}
              </p>
            </div>
          )}

          {/* Display parsed voice command result if available */}
          {latestResult && (
            <div className="mt-3 pt-3 border-top border-light">
              <h6 className="fs-7 text-uppercase tracking-wider text-muted fw-bold mb-2" style={{ fontSize: '0.75rem' }}>
                Command Analysis
              </h6>
              
              <div className="bg-light p-2.5 rounded-3 d-flex flex-column gap-2" style={{ fontSize: '0.85rem' }}>
                {latestResult.command && (
                  <div className="d-flex align-items-baseline gap-2">
                    <span className="text-muted text-nowrap" style={{ width: '80px' }}>Command:</span>
                    <span className="fw-semibold text-primary">{latestResult.command}</span>
                  </div>
                )}

                {latestResult.parsed_action && (
                  <div className="d-flex align-items-baseline gap-2">
                    <span className="text-muted text-nowrap" style={{ width: '80px' }}>Action:</span>
                    <span className="badge bg-secondary-subtle text-secondary border border-secondary-subtle">
                      {latestResult.parsed_action.action} ➔ {latestResult.parsed_action.target}
                    </span>
                  </div>
                )}

                {latestResult.message && (
                  <div className="d-flex align-items-baseline gap-2">
                    <span className="text-muted text-nowrap" style={{ width: '80px' }}>Message:</span>
                    <span className="text-secondary">{latestResult.message}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </Card.Body>
    </Card>

  );
};
export default TranscriptPanel;
