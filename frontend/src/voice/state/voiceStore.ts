import { create } from 'zustand';
import { VoiceState } from '../types/voice';

const initialState = {
  status: 'IDLE' as const,
  permissionStatus: 'prompt' as const,
  listenerRunning: false,
  listenerStatus: 'idle' as const,
  transcript: '',
  partialTranscript: '',
  finalTranscript: '',
  processing: false,
  latestResult: null,
  error: null,
  connectionState: 'DISCONNECTED' as const,
};

export const useVoiceStore = create<VoiceState>()((set) => ({
  ...initialState,

  setVoiceStatus: (status) => set({ status }),
  setPermissionStatus: (permissionStatus) => set({ permissionStatus }),
  setTranscript: (transcript) => set({ transcript }),
  setPartialTranscript: (partialTranscript) => set({ partialTranscript }),
  setFinalTranscript: (finalTranscript) => set({ finalTranscript }),
  setProcessing: (processing) => set({ processing }),
  setListenerRunning: (listenerRunning) => set({ listenerRunning }),
  setListenerStatus: (listenerStatus) => set({ listenerStatus }),
  setVoiceResult: (latestResult) => set({ latestResult }),
  setError: (error) => set({ error }),
  setConnectionState: (connectionState) => set({ connectionState }),
  clearError: () => set({ error: null }),
  reset: () => set(initialState),
}));
