export type WebSocketConnectionState =
  | 'DISCONNECTED'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'RECONNECTING'
  | 'ERROR';

export interface WebSocketEnvelope<T = unknown> {
  type: string;
  event?: string;
  requestId?: string;
  timestamp?: string;
  payload?: T;
}

export type WebSocketListener<T = any> = (envelope: WebSocketEnvelope<T>) => void;
export type StateChangeListener = (state: WebSocketConnectionState) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private state: WebSocketConnectionState = 'DISCONNECTED';
  private listeners: Set<WebSocketListener> = new Set();
  private stateListeners: Set<StateChangeListener> = new Set();
  
  private maxReconnectAttempts: number;
  private reconnectAttempts = 0;
  private reconnectDelay: number;
  private reconnectTimer: number | null = null;
  private explicitlyClosed = false;

  constructor(url?: string, options?: { maxReconnectAttempts?: number; reconnectDelay?: number }) {
    const defaultUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
    this.url = url || defaultUrl;
    this.maxReconnectAttempts = options?.maxReconnectAttempts ?? 5;
    this.reconnectDelay = options?.reconnectDelay ?? 1000;
  }

  public getState(): WebSocketConnectionState {
    return this.state;
  }

  public connect(): void {
    if (this.ws && (this.state === 'CONNECTED' || this.state === 'CONNECTING')) {
      return; // Prevent duplicate connection
    }

    this.explicitlyClosed = false;
    this.setState('CONNECTING');

    try {
      this.ws = new WebSocket(this.url);
      this.setupHandlers();
    } catch (error) {
      this.setState('ERROR');
      this.handleReconnect();
    }
  }

  public disconnect(): void {
    this.explicitlyClosed = true;
    this.clearReconnect();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.setState('DISCONNECTED');
  }

  public reconnect(): void {
    this.disconnect();
    this.connect();
  }

  public send<T>(type: string, payload?: T, event?: string, requestId?: string): void {
    if (!this.ws || this.state !== 'CONNECTED') {
      throw new Error('WebSocket is not connected');
    }

    const envelope: WebSocketEnvelope<T> = {
      type,
      event,
      requestId,
      timestamp: new Date().toISOString(),
      payload
    };

    this.ws.send(JSON.stringify(envelope));
  }

  public onMessage<T>(listener: WebSocketListener<T>): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  public onStateChange(listener: StateChangeListener): () => void {
    this.stateListeners.add(listener);
    // Emit initial state
    listener(this.state);
    return () => {
      this.stateListeners.delete(listener);
    };
  }

  private setState(state: WebSocketConnectionState): void {
    this.state = state;
    this.stateListeners.forEach((listener) => listener(state));
  }

  private setupHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.setState('CONNECTED');
    };

    this.ws.onclose = () => {
      if (this.explicitlyClosed) {
        this.setState('DISCONNECTED');
      } else {
        this.setState('DISCONNECTED');
        this.handleReconnect();
      }
    };

    this.ws.onerror = () => {
      this.setState('ERROR');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketEnvelope;
        this.listeners.forEach((listener) => {
          try {
            listener(data);
          } catch (e) {
            // Prevent listener failures from halting processing
          }
        });
      } catch (error) {
        // Safe handle malformed JSON
      }
    };
  }

  private handleReconnect(): void {
    if (this.explicitlyClosed) return;
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }

    this.clearReconnect();
    this.setState('RECONNECTING');
    this.reconnectAttempts++;

    // Exponential backoff
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    this.reconnectTimer = window.setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearReconnect(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
export default WebSocketClient;
