import React from 'react';
import { Button } from '../../../components/common';
import { VoiceControlProps } from './VoiceControl.types';

export const VoiceControl: React.FC<VoiceControlProps> = ({
  isListening,
  isProcessing,
  disabled = false,
  onStart,
  onStop,
  className = ''
}) => {
  const handleClick = () => {
    if (isListening) {
      onStop();
    } else {
      onStart();
    }
  };

  const variant = isListening ? 'danger' : 'primary';
  const icon = isListening ? 'bi-stop-fill' : 'bi-mic-fill';
  const label = isListening ? 'Stop Listening' : 'Start Listening';

  return (
    <Button
      variant={variant}
      icon={isProcessing ? undefined : icon}
      loading={isProcessing}
      loadingText="Processing..."
      disabled={disabled}
      onClick={handleClick}
      aria-label={label}
      className={`d-inline-flex align-items-center gap-1 ${className}`}
    >
      {label}
    </Button>
  );
};
export default VoiceControl;
