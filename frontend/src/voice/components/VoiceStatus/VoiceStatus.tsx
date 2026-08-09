import React from 'react';
import { VoiceStatusProps } from './VoiceStatus.types';
import { VoiceStatus as VoiceStatusType } from '../../types/voice';

const STATUS_MESSAGES: Record<VoiceStatusType, string> = {
  IDLE: 'Ready',
  REQUESTING_PERMISSION: 'Microphone permission required',
  READY: 'Ready to listen',
  LISTENING: 'Listening...',
  PROCESSING: 'Processing...',
  TRANSCRIBING: 'Transcribing...',
  COMPLETED: 'Completed',
  ERROR: 'Voice interaction failed',
  DISCONNECTED: 'Voice service unavailable'
};

const STATUS_VARIANTS: Record<VoiceStatusType, string> = {
  IDLE: 'text-muted',
  REQUESTING_PERMISSION: 'text-warning',
  READY: 'text-success',
  LISTENING: 'text-primary fw-semibold',
  PROCESSING: 'text-info fw-semibold',
  TRANSCRIBING: 'text-info fw-semibold',
  COMPLETED: 'text-success',
  ERROR: 'text-danger',
  DISCONNECTED: 'text-danger'
};

const STATUS_ICONS: Record<VoiceStatusType, string> = {
  IDLE: 'bi-mic-mute',
  REQUESTING_PERMISSION: 'bi-shield-lock',
  READY: 'bi-mic',
  LISTENING: 'bi-record-fill text-danger pulse',
  PROCESSING: 'bi-arrow-repeat spin',
  TRANSCRIBING: 'bi-translate',
  COMPLETED: 'bi-check-circle-fill',
  ERROR: 'bi-exclamation-octagon',
  DISCONNECTED: 'bi-wifi-off'
};

export const VoiceStatus: React.FC<VoiceStatusProps> = ({
  status,
  className = ''
}) => {
  const message = STATUS_MESSAGES[status] || STATUS_MESSAGES.IDLE;
  const variantClass = STATUS_VARIANTS[status] || STATUS_VARIANTS.IDLE;
  const iconClass = STATUS_ICONS[status] || STATUS_ICONS.IDLE;

  return (
    <div 
      className={`d-flex align-items-center gap-2 ${variantClass} ${className}`}
      aria-live="polite"
      role="status"
    >
      <i className={`bi ${iconClass}`} aria-hidden="true"></i>
      <span className="voice-status-text">{message}</span>
    </div>
  );
};
export default VoiceStatus;
