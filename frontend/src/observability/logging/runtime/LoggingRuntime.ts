import type { ILoggingRuntime } from '../interfaces/logging-runtime';
import type { ILoggingProvider } from '../interfaces/logging-provider';
import type { ILogger } from '../interfaces/logger';
import type { ILogSink } from '../interfaces/log-sink';
import { LoggingProvider } from '../provider/LoggingProvider';
import type { LogRecord, LogLevelValue } from '../models/log';
import type { LoggingStatistics, LoggingDiagnostics } from '../models/statistics';
import type { LogOptions } from '../models/logger';

export class LoggingRuntime implements ILoggingRuntime {
  private readonly _provider: ILoggingProvider;

  constructor(provider?: ILoggingProvider) {
    this._provider = provider || new LoggingProvider();
  }

  public provider(): ILoggingProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): string {
    return this._provider.getState();
  }

  public getLogger(name: string): ILogger {
    return this._provider.getLogger(name);
  }

  public registerLogger(name: string, config?: { minLevel?: LogLevelValue }): void {
    this._provider.registerLogger(name, config);
  }

  public unregisterLogger(name: string): void {
    this._provider.unregisterLogger(name);
  }

  public registerSink(sink: ILogSink): void {
    this._provider.registerSink(sink);
  }

  public unregisterSink(sinkId: string): void {
    this._provider.unregisterSink(sinkId);
  }

  public getSink(sinkId: string): ILogSink | null {
    return this._provider.getSink(sinkId);
  }

  public listSinks(): ReadonlyArray<ILogSink> {
    return this._provider.listSinks();
  }

  public clearSinks(): void {
    this._provider.clearSinks();
  }

  public log(recordInput: {
    level: LogLevelValue;
    message: string;
    loggerName: string;
    options?: LogOptions;
  }): void {
    this._provider.log(recordInput);
  }

  public flush(): Promise<void> {
    return this._provider.flush();
  }

  public getRecentLogs(limit?: number): ReadonlyArray<LogRecord> {
    return this._provider.getRecentLogs(limit);
  }

  public getLogsByLevel(level: LogLevelValue): ReadonlyArray<LogRecord> {
    return this._provider.getLogsByLevel(level);
  }

  public getLogsByLogger(loggerName: string): ReadonlyArray<LogRecord> {
    return this._provider.getLogsByLogger(loggerName);
  }

  public getLogsByCorrelationId(correlationId: string): ReadonlyArray<LogRecord> {
    return this._provider.getLogsByCorrelationId(correlationId);
  }

  public clearHistory(): void {
    this._provider.clearHistory();
  }

  public getStatistics(): LoggingStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): LoggingDiagnostics {
    return this._provider.getDiagnostics();
  }
}
