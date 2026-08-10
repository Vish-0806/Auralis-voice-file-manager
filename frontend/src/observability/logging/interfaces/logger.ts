import type { LogLevelValue } from '../models/log';
import type { LogContext, LogOptions } from '../models/logger';

export interface ILogger {
  getName(): string;
  isEnabled(level: LogLevelValue): boolean;
  child(context: LogContext): ILogger;

  trace(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void;
  debug(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void;
  info(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void;
  warn(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void;
  error(message: string, errorOrMetadata?: Error | Record<string, unknown> | LogOptions, metadata?: Record<string, unknown>): void;
  fatal(message: string, errorOrMetadata?: Error | Record<string, unknown> | LogOptions, metadata?: Record<string, unknown>): void;
}
