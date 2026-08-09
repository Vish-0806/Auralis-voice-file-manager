import { VoiceCommandResponse } from '../../services/api/voiceService';

export type VoiceStatus =
  | 'IDLE'
  | 'REQUESTING_PERMISSION'
  | 'READY'
  | 'LISTENING'
  | 'PROCESSING'
  | 'TRANSCRIBING'
  | 'COMPLETED'
  | 'ERROR'
  | 'DISCONNECTED';

export type ListenerStatus = 'running' | 'stopped';

export interface VoiceError {
  type: 'permission_denied' | 'permission_dismissed' | 'unsupported' | 'network' | 'timeout' | 'unknown';
  message: string;
  originalError?: unknown;
}

export interface Transcript {
  id: string;
  text: string;
  partial: boolean;
  timestamp: number;
}

export interface VoiceSession {
  id: string;
  startedAt: number;
}

export interface VoiceCapabilities {
  audioInput: boolean;
  permissionGranted: boolean;
}

export interface VoiceState {
  status: VoiceStatus;
  permissionStatus: PermissionState | 'prompt' | 'unavailable';
  listenerRunning: boolean;
  listenerStatus: 'idle' | 'loading' | 'running' | 'stopped' | 'error';
  transcript: string;
  partialTranscript: string;
  finalTranscript: string;
  processing: boolean;
  latestResult: VoiceCommandResponse | null;
  error: VoiceError | null;
  connectionState: 'CONNECTED' | 'DISCONNECTED' | 'CONNECTING' | 'RECONNECTING' | 'ERROR';

  // Actions
  setVoiceStatus: (status: VoiceStatus) => void;
  setPermissionStatus: (status: PermissionState | 'prompt' | 'unavailable') => void;
  setTranscript: (text: string) => void;
  setPartialTranscript: (text: string) => void;
  setFinalTranscript: (text: string) => void;
  setProcessing: (value: boolean) => void;
  setListenerRunning: (value: boolean) => void;
  setListenerStatus: (status: 'idle' | 'loading' | 'running' | 'stopped' | 'error') => void;
  setVoiceResult: (result: VoiceCommandResponse | null) => void;
  setError: (error: VoiceError | null) => void;
  setConnectionState: (state: 'CONNECTED' | 'DISCONNECTED' | 'CONNECTING' | 'RECONNECTING' | 'ERROR') => void;
  clearError: () => void;
  reset: () => void;
}
