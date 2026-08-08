import { apiClient } from './client';
import { ENDPOINTS } from './endpoints';

export interface AssistantRequestPayload {
  text: string;
  source?: string;
  session_id?: string;
}

export interface AssistantResponsePayload {
  response: string;
  speak_message?: string;
  actions_taken?: any[];
  status?: string;
}

export interface HealthResponsePayload {
  status: string;
  version: string;
  timestamp: string;
}

export interface PlatformInfoPayload {
  system: string;
  release: string;
  version: string;
  machine: string;
  python_version: string;
}

export interface StatusResponsePayload {
  platform: PlatformInfoPayload;
  loaded_capabilities: string[];
  assistant_status: string;
}

export const assistantService = {
  sendMessage(payload: AssistantRequestPayload): Promise<AssistantResponsePayload> {
    return apiClient.post<AssistantResponsePayload>(ENDPOINTS.ASSISTANT, payload);
  },

  sendTextCommand(command: string): Promise<any> {
    return apiClient.post<any>(ENDPOINTS.COMMAND, { command });
  },

  getHealth(): Promise<HealthResponsePayload> {
    return apiClient.get<HealthResponsePayload>(ENDPOINTS.HEALTH);
  },

  getStatus(): Promise<StatusResponsePayload> {
    return apiClient.get<StatusResponsePayload>(ENDPOINTS.STATUS);
  }
};
export default assistantService;
