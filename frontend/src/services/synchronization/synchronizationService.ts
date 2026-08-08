import { WebSocketClient, WebSocketEnvelope } from '../websocket/WebSocketClient';
import { useUIStore } from '../../state/stores/uiStore';
import { useAssistantStore } from '../../state/stores/assistantStore';
import { useFilesStore } from '../../state/stores/filesStore';

export type SyncState = 'IDLE' | 'SYNCING' | 'SYNCED' | 'STALE' | 'ERROR';

export class SynchronizationService {
  private wsClient: WebSocketClient;
  private syncState: SyncState = 'IDLE';
  private stateListeners: Set<(state: SyncState) => void> = new Set();
  private unsubscribeMessage: (() => void) | null = null;
  private unsubscribeState: (() => void) | null = null;

  constructor(wsClient: WebSocketClient) {
    this.wsClient = wsClient;
  }

  public getSyncState(): SyncState {
    return this.syncState;
  }

  public start(): void {
    this.setSyncState('SYNCING');
    
    // Subscribe to WebSocket messages
    this.unsubscribeMessage = this.wsClient.onMessage((envelope) => {
      this.handleSyncMessage(envelope);
    });

    // Subscribe to WebSocket connection status
    this.unsubscribeState = this.wsClient.onStateChange((wsState) => {
      if (wsState === 'CONNECTED') {
        this.setSyncState('SYNCED');
      } else if (wsState === 'RECONNECTING' || wsState === 'CONNECTING') {
        this.setSyncState('SYNCING');
      } else if (wsState === 'ERROR') {
        this.setSyncState('ERROR');
      } else {
        this.setSyncState('STALE');
      }
    });

    this.wsClient.connect();
  }

  public stop(): void {
    if (this.unsubscribeMessage) {
      this.unsubscribeMessage();
      this.unsubscribeMessage = null;
    }
    if (this.unsubscribeState) {
      this.unsubscribeState();
      this.unsubscribeState = null;
    }
    this.wsClient.disconnect();
    this.setSyncState('IDLE');
  }

  public onSyncStateChange(listener: (state: SyncState) => void): () => void {
    this.stateListeners.add(listener);
    listener(this.syncState);
    return () => {
      this.stateListeners.delete(listener);
    };
  }

  private setSyncState(state: SyncState): void {
    this.syncState = state;
    this.stateListeners.forEach((listener) => listener(state));
  }

  private handleSyncMessage(envelope: WebSocketEnvelope): void {
    const { type, payload } = envelope;

    switch (type) {
      case 'ASSISTANT_STREAM_CHUNK':
        if (payload && typeof payload === 'object' && 'chunk' in payload) {
          const chunk = (payload as { chunk: string }).chunk;
          const messages = useAssistantStore.getState().messages;
          if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.role === 'assistant') {
              useAssistantStore.getState().updateMessage(lastMessage.id, {
                content: lastMessage.content + chunk
              });
            }
          }
        }
        break;
      
      case 'FILES_CHANGED':
        if (payload && typeof payload === 'object' && 'directory' in payload) {
          const dir = (payload as { directory: string }).directory;
          useFilesStore.getState().setCurrentDirectory(dir);
        }
        break;

      case 'WORKSPACE_UPDATED':
        if (payload && typeof payload === 'object' && 'status' in payload) {
          const status = (payload as { status: 'idle' | 'loading' | 'success' | 'error' }).status;
          useUIStore.getState().setGlobalLoading(status === 'loading');
        }
        break;

      default:
        break;
    }
  }
}

export const syncService = new SynchronizationService(new WebSocketClient());
export default syncService;
