import type { ILogger } from './logger';
import type { ILogSink } from './log-sink';
import type { LogRecord, LogLevelValue } from '../models/log';
import type { LoggingStatistics, LoggingDiagnostics } from '../models/statistics';
import type { LogOptions } from '../models/logger';

export interface ILoggingProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;

  getLogger(name: string): ILogger;
  registerLogger(name: string, config?: { minLevel?: LogLevelValue }): void;
  unregisterLogger(name: string): void;

  registerSink(sink: ILogSink): void;
  unregisterSink(sinkId: string): void;
  getSink(sinkId: string): ILogSink | null;
  listSinks(): ReadonlyArray<ILogSink>;
  clearSinks(): void;

  log(recordInput: {
    level: LogLevelValue;
    message: string;
    loggerName: string;
    options?: LogOptions;
  }): void;

  flush(): Promise<void>;

  getRecentLogs(limit?: number): ReadonlyArray<LogRecord>;
  getLogsByLevel(level: LogLevelValue): ReadonlyArray<LogRecord>;
  getLogsByLogger(loggerName: string): ReadonlyArray<LogRecord>;
  getLogsByCorrelationId(correlationId: string): ReadonlyArray<LogRecord>;
  clearHistory(): void;

  getStatistics(): LoggingStatistics;
  getDiagnostics(): LoggingDiagnostics;
}
