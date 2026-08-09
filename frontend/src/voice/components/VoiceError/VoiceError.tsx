import React from 'react';
import { Alert } from '../../../components/common';
import { VoiceErrorProps } from './VoiceError.types';

export const VoiceError: React.FC<VoiceErrorProps> = ({
  error,
  onClear,
  className = ''
}) => {
  if (!error) return null;

  // Map internal error type to Bootstrap icons or user friendly classes
  let iconClass = 'bi-exclamation-triangle-fill';
  if (error.type === 'permission_denied') {
    iconClass = 'bi-mic-mute-fill';
  } else if (error.type === 'network') {
    iconClass = 'bi-wifi-off';
  }

  return (
    <Alert
      variant="danger"
      dismissible={!!onClear}
      onClose={onClear}
      className={`d-flex align-items-center gap-2 ${className}`}
    >
      <i className={`bi ${iconClass} fs-5`} aria-hidden="true"></i>
      <div>
        <strong className="d-block">Voice Service Error</strong>
        <span className="small">{error.message}</span>
      </div>
    </Alert>
  );
};
export default VoiceError;
