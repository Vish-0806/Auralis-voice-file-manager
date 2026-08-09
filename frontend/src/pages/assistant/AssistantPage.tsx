import React, { useEffect } from 'react';
import { useLayout } from '../../layouts/AppLayout';
import { 
  VoiceControl, 
  VoiceStatus, 
  VoiceVisualizer, 
  TranscriptPanel, 
  ListenerControl, 
  VoiceError 
} from '../../voice';
import { useVoice, useVoiceListener } from '../../voice';

export const AssistantPage: React.FC = () => {
  const { setDescription } = useLayout();
  const {
    status,
    partialTranscript,
    finalTranscript,
    error: voiceError,
    isListening,
    isProcessing,
    latestResult,
    startListening,
    stopListening,
    clearError
  } = useVoice();

  const {
    isRunning: listenerRunning,
    loading: listenerLoading,
    start: startListener,
    stop: stopListener,
    refresh: refreshListener
  } = useVoiceListener();

  useEffect(() => {
    setDescription('Interactive natural language conversational hub.');
    // Check listener status on mount
    refreshListener();
  }, [setDescription]);

  return (
    <div className="container-fluid px-0">
      {voiceError && (
        <div className="row mb-3">
          <div className="col-12">
            <VoiceError error={voiceError} onClear={clearError} />
          </div>
        </div>
      )}

      <div className="row g-4">
        {/* Main Voice Hub Area */}
        <div className="col-12 col-lg-8">
          <div className="card border-0 shadow-sm p-4 mb-4">
            <div className="d-flex align-items-center justify-content-between mb-4">
              <div>
                <h5 className="mb-1 text-secondary fw-semibold">Assistant Hub</h5>
                <p className="text-muted small mb-0">Use one-shot voice commands to query and manage files.</p>
              </div>
              <VoiceStatus status={status} />
            </div>

            <div className="d-flex flex-column align-items-center justify-content-center py-4 bg-light rounded-3 border border-dashed mb-4">
              <VoiceVisualizer status={status} className="mb-3" />
              <VoiceControl
                isListening={isListening}
                isProcessing={isProcessing}
                onStart={startListening}
                onStop={stopListening}
              />
            </div>
          </div>

          <TranscriptPanel
            partialTranscript={partialTranscript}
            finalTranscript={finalTranscript}
            latestResult={latestResult}
            processing={isProcessing}
          />
        </div>

        {/* Configuration / Listener Settings Sidebar */}
        <div className="col-12 col-lg-4">
          <div className="d-flex flex-column gap-4">
            <ListenerControl
              isRunning={listenerRunning}
              loading={listenerLoading}
              onStart={startListener}
              onStop={stopListener}
              onRefresh={refreshListener}
            />

            <div className="card border-0 shadow-sm p-4">
              <h6 className="text-secondary mb-3 fw-semibold">
                <i className="bi bi-info-circle text-primary me-2"></i>
                Supported Commands
              </h6>
              <ul className="list-unstyled mb-0 d-flex flex-column gap-2" style={{ fontSize: '0.85rem' }}>
                <li className="d-flex gap-2">
                  <i className="bi bi-check2-circle text-success"></i>
                  <span>"Search for PDF files"</span>
                </li>
                <li className="d-flex gap-2">
                  <i className="bi bi-check2-circle text-success"></i>
                  <span>"Create a folder named Archives"</span>
                </li>
                <li className="d-flex gap-2">
                  <i className="bi bi-check2-circle text-success"></i>
                  <span>"Move invoice.csv to finance"</span>
                </li>
                <li className="d-flex gap-2">
                  <i className="bi bi-check2-circle text-success"></i>
                  <span>"Delete temp directory"</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default AssistantPage;
