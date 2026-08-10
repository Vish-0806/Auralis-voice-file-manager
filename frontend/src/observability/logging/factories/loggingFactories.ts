import { type LogRecord, type LogLevelValue, LogLevel, type StructuredError } from '../models/log';
import type { LogOptions } from '../models/logger';
import { freezeDeepSafe } from '../../models/monitoring';
import { LoggingValidationError } from '../errors/LoggingErrors';

let recordCounter = 0;
function generateUniqueId(): string {
  recordCounter += 1;
  return `log_${Date.now()}_${recordCounter}_${Math.random().toString(36).substring(2, 7)}`;
}

export function createStructuredError(err: unknown): StructuredError {
  if (err instanceof Error) {
    const res: any = {
      name: err.name,
      message: err.message,
      stack: err.stack
    };
    if ('code' in err) {
      res.code = (err as any).code;
    }
    if ('cause' in err) {
      res.cause = (err as any).cause;
    }
    return res;
  }
  return {
    name: 'Error',
    message: String(err)
  };
}

export function createLogRecord(input: {
  level: LogLevelValue;
  message: string;
  loggerName: string;
  options?: LogOptions;
}): LogRecord {
  if (!input.loggerName || !input.loggerName.trim()) {
    throw new LoggingValidationError('Logger name is required and cannot be empty.');
  }
  if (!Object.values(LogLevel).includes(input.level)) {
    throw new LoggingValidationError(`Invalid log level: ${input.level}`);
  }
  if (input.message === undefined || input.message === null) {
    throw new LoggingValidationError('Log message is required.');
  }

  const options = input.options || {};
  const context = options.context;
  const metadata = options.metadata;
  
  let errorRepresentation = undefined;
  if (options.error) {
    errorRepresentation = createStructuredError(options.error);
  }

  const record: LogRecord = {
    id: generateUniqueId(),
    timestamp: Date.now(),
    level: input.level,
    message: input.message,
    loggerName: input.loggerName,
    context: context ? { ...context } : undefined,
    metadata: metadata ? { ...metadata } : undefined,
    error: errorRepresentation,
    correlationId: options.correlationId ?? context?.correlationId,
    requestId: options.requestId ?? context?.requestId,
    sessionId: options.sessionId ?? context?.sessionId,
    pluginId: options.pluginId ?? context?.pluginId,
    componentId: options.componentId ?? context?.componentId,
    operation: options.operation ?? context?.operation
  };

  return freezeDeepSafe(record);
}
