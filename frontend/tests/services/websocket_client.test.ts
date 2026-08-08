import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { WebSocketClient, WebSocketConnectionState } from '../../src/services/websocket/WebSocketClient';

// Setup Mock WebSocket class globally for testing
class MockWebSocket {
  public url: string;
  public onopen: (() => void) | null = null;
  public onclose: (() => void) | null = null;
  public onerror: (() => void) | null = null;
  public onmessage: ((e: { data: string }) => void) | null = null;
  public readyState = 0;
  public send = vi.fn();
  public close = vi.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  static instances: MockWebSocket[] = [];
}

const originalWebSocket = global.WebSocket;

describe('WebSocketClient', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    global.WebSocket = MockWebSocket as any;
    vi.useFakeTimers();
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    vi.restoreAllMocks();
  });

  it('should initialize with disconnected state', () => {
    const client = new WebSocketClient('ws://test-url');
    expect(client.getState()).toBe('DISCONNECTED');
  });

  it('should transition to CONNECTING, then CONNECTED', () => {
    const client = new WebSocketClient('ws://test-url');
    let lastState: WebSocketConnectionState = 'DISCONNECTED';
    client.onStateChange((state) => {
      lastState = state;
    });

    client.connect();
    expect(lastState).toBe('CONNECTING');
    expect(MockWebSocket.instances).toHaveLength(1);

    const wsInstance = MockWebSocket.instances[0];
    wsInstance.onopen?.();
    expect(lastState).toBe('CONNECTED');
  });

  it('should prevent duplicate connections when connecting or connected', () => {
    const client = new WebSocketClient('ws://test-url');
    client.connect();
    client.connect();
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it('should execute message listeners when socket receives data', () => {
    const client = new WebSocketClient('ws://test-url');
    let receivedPayload: any = null;
    
    client.onMessage((envelope) => {
      receivedPayload = envelope.payload;
    });

    client.connect();
    MockWebSocket.instances[0].onopen?.();
    
    MockWebSocket.instances[0].onmessage?.({
      data: JSON.stringify({ type: 'TEST', payload: { value: 42 } })
    });

    expect(receivedPayload).toEqual({ value: 42 });
  });

  it('should handle malformed JSON messages without crashing', () => {
    const client = new WebSocketClient('ws://test-url');
    client.connect();
    MockWebSocket.instances[0].onopen?.();
    
    expect(() => {
      MockWebSocket.instances[0].onmessage?.({ data: 'invalid-json' });
    }).not.toThrow();
  });

  it('should clean up listeners correctly', () => {
    const client = new WebSocketClient('ws://test-url');
    let count = 0;
    const unsub = client.onMessage(() => {
      count++;
    });

    client.connect();
    MockWebSocket.instances[0].onopen?.();
    
    MockWebSocket.instances[0].onmessage?.({ data: JSON.stringify({ type: 'TEST' }) });
    expect(count).toBe(1);

    unsub();
    MockWebSocket.instances[0].onmessage?.({ data: JSON.stringify({ type: 'TEST' }) });
    expect(count).toBe(1);
  });

  it('should trigger reconnect loops with exponential backoff on connection failure', () => {
    const client = new WebSocketClient('ws://test-url', { maxReconnectAttempts: 3, reconnectDelay: 50 });
    let lastState: WebSocketConnectionState = 'DISCONNECTED';
    client.onStateChange((state) => {
      lastState = state;
    });

    client.connect();
    MockWebSocket.instances[0].onclose?.();

    expect(lastState).toBe('RECONNECTING');
    
    // First backoff is 50ms
    vi.advanceTimersByTime(50);
    expect(MockWebSocket.instances).toHaveLength(2);

    // Close second attempt to trigger third attempt
    MockWebSocket.instances[1].onclose?.();
    
    // Second backoff is 100ms
    vi.advanceTimersByTime(100);
    expect(MockWebSocket.instances).toHaveLength(3);
  });

  it('should transition to DISCONNECTED when closed explicitly', () => {
    const client = new WebSocketClient('ws://test-url');
    client.connect();
    MockWebSocket.instances[0].onopen?.();
    
    client.disconnect();
    expect(client.getState()).toBe('DISCONNECTED');
    expect(MockWebSocket.instances[0].close).toHaveBeenCalled();
  });
});
