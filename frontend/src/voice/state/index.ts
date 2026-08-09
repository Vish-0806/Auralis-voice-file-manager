import { VoiceState } from '../types/voice';

export * from './voiceStore';

// Selectors
export const selectVoiceStatus = (state: VoiceState) => state.status;
export const selectPermissionStatus = (state: VoiceState) => state.permissionStatus;
export const selectListenerRunning = (state: VoiceState) => state.listenerRunning;
export const selectListenerStatus = (state: VoiceState) => state.listenerStatus;
export const selectVoiceTranscript = (state: VoiceState) => state.transcript;
export const selectVoicePartialTranscript = (state: VoiceState) => state.partialTranscript;
export const selectVoiceFinalTranscript = (state: VoiceState) => state.finalTranscript;
export const selectVoiceProcessing = (state: VoiceState) => state.processing;
export const selectVoiceLatestResult = (state: VoiceState) => state.latestResult;
export const selectVoiceError = (state: VoiceState) => state.error;
export const selectVoiceConnectionState = (state: VoiceState) => state.connectionState;
