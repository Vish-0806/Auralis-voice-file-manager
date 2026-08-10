export const LogLevel = {
  TRACE: 'TRACE',
  DEBUG: 'DEBUG',
  INFO: 'INFO',
  WARN: 'WARN',
  ERROR: 'ERROR',
  FATAL: 'FATAL'
} as const;

export type LogLevelValue = typeof LogLevel[keyof typeof LogLevel];

export const LogLevelSeverity: Record<LogLevelValue, number> = {
  TRACE: 0,
  DEBUG: 1,
  INFO: 2,
  WARN: 3,
  ERROR: 4,
  FATAL: 5
};

export interface StructuredError {
  readonly name: string;
  readonly message: string;
  readonly stack?: string;
  readonly code?: string | number;
  readonly cause?: unknown;
}

export interface LogRecord {
  readonly id: string;
  readonly timestamp: number;
  readonly level: LogLevelValue;
  readonly message: string;
  readonly loggerName: string;
  readonly context?: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
  readonly error?: StructuredError;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly sessionId?: string;
  readonly pluginId?: string;
  readonly componentId?: string;
  readonly operation?: string;
  readonly durationMs?: number;
}
