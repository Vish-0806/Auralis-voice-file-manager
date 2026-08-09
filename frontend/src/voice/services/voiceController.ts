import { voiceService } from '../../services/api/voiceService';
import { useVoiceStore } from '../state/voiceStore';
import { VoiceError } from '../types/voice';

export const voiceController = {
  /**
   * Checks browser microphone capability and requests permission.
   */
  async checkPermission(): Promise<boolean> {
    const store = useVoiceStore.getState();
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      store.setPermissionStatus('unavailable');
      store.setError({
        type: 'unsupported',
        message: 'Speech recognition is not supported in this browser (media devices unavailable).'
      });
      return false;
    }

    try {
      store.setVoiceStatus('REQUESTING_PERMISSION');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Immediately stop the tracks since we are not capturing raw audio on client
      stream.getTracks().forEach(track => track.stop());
      
      store.setPermissionStatus('granted');
      store.setVoiceStatus('READY');
      return true;
    } catch (err: any) {
      let type: VoiceError['type'] = 'unknown';
      let message = 'An unexpected error occurred while requesting microphone permission.';

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        type = 'permission_denied';
        message = 'Microphone permission denied. Please allow microphone access in your browser settings.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        type = 'unsupported';
        message = 'No microphone device was found on this system.';
      }

      store.setPermissionStatus('denied');
      store.setVoiceStatus('ERROR');
      store.setError({ type, message, originalError: err });
      return false;
    }
  },

  /**
   * Starts a one-shot listening command.
   */
  async startListening(): Promise<void> {
    const store = useVoiceStore.getState();
    store.clearError();

    // Check permission first
    const hasPermission = await this.checkPermission();
    if (!hasPermission) return;

    try {
      store.setVoiceStatus('LISTENING');
      
      // Call backend SPEECH TO TEXT
      const response = await voiceService.listenVoice();
      
      store.setVoiceStatus('PROCESSING');
      
      if (response && response.status === 'success') {
        store.setTranscript(response.recognized_text || '');
        store.setFinalTranscript(response.recognized_text || '');
        store.setVoiceResult(response);
        store.setVoiceStatus('COMPLETED');
      } else {
        throw new Error(response?.message || 'Speech recognition failed.');
      }
    } catch (err: any) {
      store.setVoiceStatus('ERROR');
      store.setError({
        type: err.message?.toLowerCase().includes('network') ? 'network' : 'unknown',
        message: err.message || 'Failed to process voice input from the server.',
        originalError: err
      });
    }
  },

  /**
   * Resets the one-shot voice status.
   */
  stopListening(): void {
    const store = useVoiceStore.getState();
    store.setVoiceStatus('IDLE');
  },

  /**
   * Starts the continuous listener on the backend.
   */
  async startContinuousListener(): Promise<void> {
    const store = useVoiceStore.getState();
    store.setListenerStatus('loading');
    store.clearError();

    try {
      const response = await voiceService.startListener();
      if (response.status === 'success') {
        store.setListenerRunning(true);
        store.setListenerStatus('running');
      } else {
        throw new Error(response.message || 'Failed to start the continuous listener.');
      }
    } catch (err: any) {
      store.setListenerStatus('error');
      store.setError({
        type: 'network',
        message: err.message || 'Continuous listener failed to start.',
        originalError: err
      });
    }
  },

  /**
   * Stops the continuous listener on the backend.
   */
  async stopContinuousListener(): Promise<void> {
    const store = useVoiceStore.getState();
    store.setListenerStatus('loading');
    store.clearError();

    try {
      const response = await voiceService.stopListener();
      if (response.status === 'success') {
        store.setListenerRunning(false);
        store.setListenerStatus('stopped');
      } else {
        throw new Error(response.message || 'Failed to stop the continuous listener.');
      }
    } catch (err: any) {
      store.setListenerStatus('error');
      store.setError({
        type: 'network',
        message: err.message || 'Continuous listener failed to stop.',
        originalError: err
      });
    }
  },

  /**
   * Retrieves the current continuous listener status from the backend.
   */
  async refreshListenerStatus(): Promise<void> {
    const store = useVoiceStore.getState();
    
    try {
      const response = await voiceService.getListenerStatus();
      store.setListenerRunning(response.running);
      store.setListenerStatus(response.status === 'running' ? 'running' : 'stopped');
    } catch (err: any) {
      // Don't override general errors with background refresh checks, but update listener status
      store.setListenerStatus('error');
    }
  }
};
