import type { ILogger } from '../interfaces/logger';
import type { ILoggingProvider } from '../interfaces/logging-provider';
import { type LogLevelValue, LogLevel, LogLevelSeverity } from '../models/log';
import type { LogContext, LogOptions } from '../models/logger';
import { LoggingValidationError } from '../errors/LoggingErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class Logger implements ILogger {
  constructor(
    private readonly name: string,
    private readonly provider: ILoggingProvider,
    private readonly config: { minLevel?: LogLevelValue } = {},
    private readonly context: LogContext = {}
  ) {}

  public getName(): string {
    return this.name;
  }

  public isEnabled(level: LogLevelValue): boolean {
    const loggerMin = this.config.minLevel;
    if (loggerMin) {
      return LogLevelSeverity[level] >= LogLevelSeverity[loggerMin];
    }
    return true;
  }

  public child(childContext: LogContext): ILogger {
    if (!childContext) {
      throw new LoggingValidationError('Child logger context cannot be null or undefined.');
    }
    const mergedContext = freezeDeepSafe({
      ...this.context,
      ...childContext
    });
    return new Logger(this.name, this.provider, this.config, mergedContext);
  }
  private logWithLevel(level: LogLevelValue, message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void {
    let options: LogOptions = {};
    if (metadataOrOptions) {
      const optionsKeys = [
        'metadata',
        'context',
        'error',
        'correlationId',
        'requestId',
        'sessionId',
        'pluginId',
        'componentId',
        'operation'
      ];
      const hasOptionsKey = Object.keys(metadataOrOptions).some(k => optionsKeys.includes(k));
      if (hasOptionsKey) {
        options = metadataOrOptions as LogOptions;
      } else {
        options = { metadata: metadataOrOptions as Record<string, unknown> };
      }
    }

    const mergedContext = {
      ...this.context,
      ...options.context,
      ...context
    };

    const finalOptions: LogOptions = {
      ...options,
      context: mergedContext,
      correlationId: options.correlationId ?? mergedContext.correlationId,
      requestId: options.requestId ?? mergedContext.requestId,
      sessionId: options.sessionId ?? mergedContext.sessionId,
      pluginId: options.pluginId ?? mergedContext.pluginId,
      componentId: options.componentId ?? mergedContext.componentId,
      operation: options.operation ?? mergedContext.operation
    };

    this.provider.log({
      level,
      message,
      loggerName: this.name,
      options: finalOptions
    });
  }

  public trace(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void {
    this.logWithLevel(LogLevel.TRACE, message, metadataOrOptions, context);
  }

  public debug(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void {
    this.logWithLevel(LogLevel.DEBUG, message, metadataOrOptions, context);
  }

  public info(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void {
    this.logWithLevel(LogLevel.INFO, message, metadataOrOptions, context);
  }

  public warn(message: string, metadataOrOptions?: Record<string, unknown> | LogOptions, context?: LogContext): void {
    this.logWithLevel(LogLevel.WARN, message, metadataOrOptions, context);
  }

  public error(message: string, errorOrMetadata?: Error | Record<string, unknown> | LogOptions, metadata?: Record<string, unknown>): void {
    let options: LogOptions = {};
    if (errorOrMetadata instanceof Error) {
      options = { error: errorOrMetadata, metadata };
    } else if (errorOrMetadata) {
      if ('metadata' in errorOrMetadata || 'context' in errorOrMetadata || 'error' in errorOrMetadata) {
        options = errorOrMetadata as LogOptions;
      } else {
        options = { metadata: errorOrMetadata as Record<string, unknown> };
      }
    }
    this.logWithLevel(LogLevel.ERROR, message, options);
  }

  public fatal(message: string, errorOrMetadata?: Error | Record<string, unknown> | LogOptions, metadata?: Record<string, unknown>): void {
    let options: LogOptions = {};
    if (errorOrMetadata instanceof Error) {
      options = { error: errorOrMetadata, metadata };
    } else if (errorOrMetadata) {
      if ('metadata' in errorOrMetadata || 'context' in errorOrMetadata || 'error' in errorOrMetadata) {
        options = errorOrMetadata as LogOptions;
      } else {
        options = { metadata: errorOrMetadata as Record<string, unknown> };
      }
    }
    this.logWithLevel(LogLevel.FATAL, message, options);
  }
}
