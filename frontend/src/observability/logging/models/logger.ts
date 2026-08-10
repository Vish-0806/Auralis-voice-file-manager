export interface LogContext {
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly sessionId?: string;
  readonly pluginId?: string;
  readonly componentId?: string;
  readonly userId?: string;
  readonly operation?: string;
  readonly source?: string;
  readonly [key: string]: unknown;
}

export interface LogOptions {
  readonly metadata?: Record<string, unknown>;
  readonly context?: LogContext;
  readonly error?: Error;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly sessionId?: string;
  readonly pluginId?: string;
  readonly componentId?: string;
  readonly operation?: string;
}
