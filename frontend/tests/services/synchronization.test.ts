import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SynchronizationService, SyncState } from '../../src/services/synchronization/synchronizationService';
import { useUIStore } from '../../src/state/stores/uiStore';
import { useAssistantStore } from '../../src/state/stores/assistantStore';
import { useFilesStore } from '../../src/state/stores/filesStore';

// Simple mock for WebSocketClient
class MockWebSocketClient {
  public messageCallback: ((data: any) => void) | null = null;
  public stateCallback: ((state: string) => void) | null = null;
  public connect = vi.fn();
  public disconnect = vi.fn();

  public onMessage(cb: any) {
    this.messageCallback = cb;
    return () => { this.messageCallback = null; };
  }

  public onStateChange(cb: any) {
    this.stateCallback = cb;
    return () => { this.stateCallback = null; };
  }

  public triggerMessage(type: string, payload?: any) {
    this.messageCallback?.({ type, payload });
  }

  public triggerState(state: string) {
    this.stateCallback?.(state);
  }
}

describe('SynchronizationService', () => {
  let wsClient: MockWebSocketClient;
  let sync: SynchronizationService;

  beforeEach(() => {
    wsClient = new MockWebSocketClient();
    sync = new SynchronizationService(wsClient as any);
    useUIStore.getState().reset();
    useAssistantStore.getState().reset();
    useFilesStore.getState().reset();
  });

  it('should initialize with IDLE sync state', () => {
    expect(sync.getSyncState()).toBe('IDLE');
  });

  it('should transition to SYNCING on start and call connect', () => {
    sync.start();
    expect(sync.getSyncState()).toBe('SYNCING');
    expect(wsClient.connect).toHaveBeenCalled();
  });

  it('should map WebSocket states to SyncStates correctly', () => {
    let lastState: SyncState = 'IDLE';
    sync.onSyncStateChange((s) => {
      lastState = s;
    });

    sync.start();
    expect(lastState).toBe('SYNCING');

    wsClient.triggerState('CONNECTED');
    expect(lastState).toBe('SYNCED');

    wsClient.triggerState('RECONNECTING');
    expect(lastState).toBe('SYNCING');

    wsClient.triggerState('ERROR');
    expect(lastState).toBe('ERROR');

    wsClient.triggerState('DISCONNECTED');
    expect(lastState).toBe('STALE');
  });

  it('should dispatch ASSISTANT_STREAM_CHUNK to assistantStore', () => {
    sync.start();
    wsClient.triggerState('CONNECTED');

    // Add initial assistant message
    useAssistantStore.getState().addMessage({ role: 'assistant', content: 'Hello ' });

    wsClient.triggerMessage('ASSISTANT_STREAM_CHUNK', { chunk: 'World!' });
    
    const messages = useAssistantStore.getState().messages;
    expect(messages[0].content).toBe('Hello World!');
  });

  it('should dispatch FILES_CHANGED events to filesStore', () => {
    sync.start();
    wsClient.triggerState('CONNECTED');

    wsClient.triggerMessage('FILES_CHANGED', { directory: '/downloads' });

    expect(useFilesStore.getState().currentDirectory).toBe('/downloads');
  });

  it('should dispatch WORKSPACE_UPDATED events to uiStore', () => {
    sync.start();
    wsClient.triggerState('CONNECTED');

    wsClient.triggerMessage('WORKSPACE_UPDATED', { status: 'loading' });
    expect(useUIStore.getState().globalLoading).toBe(true);

    wsClient.triggerMessage('WORKSPACE_UPDATED', { status: 'success' });
    expect(useUIStore.getState().globalLoading).toBe(false);
  });

  it('should cleanly unsubscribe on stop', () => {
    sync.start();
    sync.stop();
    expect(sync.getSyncState()).toBe('IDLE');
    expect(wsClient.disconnect).toHaveBeenCalled();
    expect(wsClient.messageCallback).toBeNull();
    expect(wsClient.stateCallback).toBeNull();
  });
});
