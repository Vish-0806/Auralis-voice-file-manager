import { apiClient } from './client';
import { ENDPOINTS } from './endpoints';

export interface VoiceCommandResponse {
  status: string;
  recognized_text?: string;
  command?: string;
  parsed_action?: {
    action: string;
    target: string;
  };
  result?: any;
  message?: string;
}

export interface ListenerStatusResponse {
  running: boolean;
  status: 'running' | 'stopped';
}

export interface ListenerStartStopResponse {
  status: string;
  message: string;
}

export const voiceService = {
  listenVoice(): Promise<VoiceCommandResponse> {
    return apiClient.get<VoiceCommandResponse>(ENDPOINTS.VOICE.LISTEN);
  },

  startListener(): Promise<ListenerStartStopResponse> {
    return apiClient.post<ListenerStartStopResponse>(ENDPOINTS.LISTENER.START);
  },

  stopListener(): Promise<ListenerStartStopResponse> {
    return apiClient.post<ListenerStartStopResponse>(ENDPOINTS.LISTENER.STOP);
  },

  getListenerStatus(): Promise<ListenerStatusResponse> {
    return apiClient.get<ListenerStatusResponse>(ENDPOINTS.LISTENER.STATUS);
  }
};
export default voiceService;
