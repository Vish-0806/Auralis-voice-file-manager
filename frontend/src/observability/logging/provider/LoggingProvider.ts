import type { ILoggingProvider } from '../interfaces/logging-provider';
import type { ILogger } from '../interfaces/logger';
import type { ILogSink } from '../interfaces/log-sink';
import { type LogRecord, type LogLevelValue, LogLevel, LogLevelSeverity } from '../models/log';
import type { LogOptions } from '../models/logger';
import type { LoggingStatistics, LoggingDiagnostics } from '../models/statistics';
import { LoggingRegistry } from '../registry/LoggingRegistry';
import {
  LoggingStateError,
  LoggingInitializationError,
  LoggingRegistrationError,
  LogSinkNotFoundError,
  LoggingValidationError
} from '../errors/LoggingErrors';
import { createLogRecord } from '../factories/loggingFactories';
import { freezeDeepSafe } from '../../models/monitoring';

export class LoggingProvider implements ILoggingProvider {
  private lifecycleState = 'UNINITIALIZED';
  private globalMinLevel: LogLevelValue = LogLevel.TRACE;
  
  private readonly registry = new LoggingRegistry(this);
  private readonly sinks = new Map<string, ILogSink>();
  private readonly history: LogRecord[] = [];
  private readonly historyCapacity = 1000;

  // Stats counters
  private totalRecords = 0;
  private traceCount = 0;
  private debugCount = 0;
  private infoCount = 0;
  private warnCount = 0;
  private errorCount = 0;
  private fatalCount = 0;
  private filteredCount = 0;
  private dispatchedCount = 0;
  private failedSinkWrites = 0;
  private lastLogTimestamp?: number;

  private ensureReady(): void {
    if (this.lifecycleState !== 'READY') {
      throw new LoggingStateError(`Logging provider is not ready (current state: ${this.lifecycleState}).`);
    }
  }

  public async initialize(): Promise<void> {
    if (this.lifecycleState === 'READY') {
      return;
    }
    if (this.lifecycleState === 'INITIALIZING' || this.lifecycleState === 'STOPPING' || this.lifecycleState === 'STOPPED') {
      throw new LoggingStateError(`Cannot initialize logging provider from state: ${this.lifecycleState}`);
    }

    this.lifecycleState = 'INITIALIZING';
    try {
      this.lifecycleState = 'READY';
    } catch (err: any) {
      this.lifecycleState = 'ERROR';
      throw new LoggingInitializationError(`Failed to initialize logging provider: ${err.message}`);
    }
  }

  public async shutdown(): Promise<void> {
    if (this.lifecycleState === 'STOPPED') {
      return;
    }
    if (this.lifecycleState === 'UNINITIALIZED') {
      throw new LoggingStateError('Cannot shutdown logging provider: it is not initialized.');
    }

    this.lifecycleState = 'STOPPING';
    try {
      await this.flush();
      for (const sink of this.sinks.values()) {
        try {
          await sink.close();
        } catch {
          // Isolate sink close errors
        }
      }
    } finally {
      this.lifecycleState = 'STOPPED';
    }
  }

  public getState(): string {
    return this.lifecycleState;
  }

  public getGlobalMinLevel(): LogLevelValue {
    return this.globalMinLevel;
  }

  public setGlobalMinLevel(level: LogLevelValue): void {
    if (!Object.values(LogLevel).includes(level)) {
      throw new LoggingValidationError(`Invalid log level: ${level}`);
    }
    this.globalMinLevel = level;
  }

  public getLogger(name: string): ILogger {
    this.ensureReady();
    return this.registry.getLogger(name);
  }

  public registerLogger(name: string, config?: { minLevel?: LogLevelValue }): void {
    this.ensureReady();
    this.registry.registerLogger(name, config);
  }

  public unregisterLogger(name: string): void {
    this.ensureReady();
    this.registry.unregisterLogger(name);
  }

  public registerSink(sink: ILogSink): void {
    this.ensureReady();
    if (!sink || !sink.id) {
      throw new LoggingValidationError('Log sink and sink ID are required.');
    }
    if (this.sinks.has(sink.id)) {
      throw new LoggingRegistrationError(`Sink with ID '${sink.id}' is already registered.`);
    }
    this.sinks.set(sink.id, sink);
  }

  public unregisterSink(sinkId: string): void {
    this.ensureReady();
    if (!this.sinks.has(sinkId)) {
      throw new LogSinkNotFoundError(`Sink with ID '${sinkId}' not found.`, sinkId);
    }
    this.sinks.delete(sinkId);
  }

  public getSink(sinkId: string): ILogSink | null {
    this.ensureReady();
    return this.sinks.get(sinkId) || null;
  }

  public listSinks(): ReadonlyArray<ILogSink> {
    this.ensureReady();
    const list = Array.from(this.sinks.values());
    list.sort((a, b) => a.id.localeCompare(b.id));
    return Object.freeze(list);
  }

  public clearSinks(): void {
    this.ensureReady();
    this.sinks.clear();
  }

  public log(recordInput: {
    level: LogLevelValue;
    message: string;
    loggerName: string;
    options?: LogOptions;
  }): void {
    this.ensureReady();
    this.totalRecords += 1;

    // 1. Global Level Filter
    if (LogLevelSeverity[recordInput.level] < LogLevelSeverity[this.globalMinLevel]) {
      this.filteredCount += 1;
      return;
    }

    // 2. Logger Level Filter
    const logger = this.registry.getLogger(recordInput.loggerName);
    if (!logger.isEnabled(recordInput.level)) {
      this.filteredCount += 1;
      return;
    }

    // 3. Create record
    const record = createLogRecord(recordInput);
    this.lastLogTimestamp = record.timestamp;

    // 4. Update level stats
    if (record.level === LogLevel.TRACE) this.traceCount += 1;
    else if (record.level === LogLevel.DEBUG) this.debugCount += 1;
    else if (record.level === LogLevel.INFO) this.infoCount += 1;
    else if (record.level === LogLevel.WARN) this.warnCount += 1;
    else if (record.level === LogLevel.ERROR) this.errorCount += 1;
    else if (record.level === LogLevel.FATAL) this.fatalCount += 1;

    // 5. Add to bounded history
    if (this.history.length >= this.historyCapacity) {
      this.history.shift();
    }
    this.history.push(record);

    // 6. Dispatch to sinks asynchronously
    for (const sink of this.sinks.values()) {
      if (sink.isEnabled() && LogLevelSeverity[record.level] >= LogLevelSeverity[sink.getMinLevel()]) {
        this.dispatchedCount += 1;
        sink.write(record).catch(() => {
          this.failedSinkWrites += 1;
        });
      }
    }
  }

  public async flush(): Promise<void> {
    if (this.lifecycleState !== 'READY' && this.lifecycleState !== 'STOPPING') {
      throw new LoggingStateError(`Cannot flush in state: ${this.lifecycleState}`);
    }
    const promises: Promise<void>[] = [];
    for (const sink of this.sinks.values()) {
      if (sink.isEnabled()) {
        promises.push(
          sink.flush().catch(() => {
            // Isolate flush errors
          })
        );
      }
    }
    await Promise.all(promises);
  }

  public getRecentLogs(limit?: number): ReadonlyArray<LogRecord> {
    this.ensureReady();
    const take = limit !== undefined ? Math.min(limit, this.history.length) : this.history.length;
    const startIndex = this.history.length - take;
    return freezeDeepSafe(this.history.slice(startIndex)) as ReadonlyArray<LogRecord>;
  }

  public getLogsByLevel(level: LogLevelValue): ReadonlyArray<LogRecord> {
    this.ensureReady();
    const filtered = this.history.filter(r => r.level === level);
    return freezeDeepSafe(filtered) as ReadonlyArray<LogRecord>;
  }

  public getLogsByLogger(loggerName: string): ReadonlyArray<LogRecord> {
    this.ensureReady();
    const filtered = this.history.filter(r => r.loggerName === loggerName);
    return freezeDeepSafe(filtered) as ReadonlyArray<LogRecord>;
  }

  public getLogsByCorrelationId(correlationId: string): ReadonlyArray<LogRecord> {
    this.ensureReady();
    const filtered = this.history.filter(r => r.correlationId === correlationId);
    return freezeDeepSafe(filtered) as ReadonlyArray<LogRecord>;
  }

  public clearHistory(): void {
    this.ensureReady();
    this.history.length = 0;
  }

  public getStatistics(): LoggingStatistics {
    this.ensureReady();
    return freezeDeepSafe({
      totalRecords: this.totalRecords,
      traceCount: this.traceCount,
      debugCount: this.debugCount,
      infoCount: this.infoCount,
      warnCount: this.warnCount,
      errorCount: this.errorCount,
      fatalCount: this.fatalCount,
      filteredCount: this.filteredCount,
      dispatchedCount: this.dispatchedCount,
      failedSinkWrites: this.failedSinkWrites,
      registeredLoggerCount: this.registry.getLoggerCount(),
      registeredSinkCount: this.sinks.size,
      lastLogTimestamp: this.lastLogTimestamp
    });
  }

  public getDiagnostics(): LoggingDiagnostics {
    this.ensureReady();
    const warnings: string[] = [];
    if (this.failedSinkWrites > 0) {
      warnings.push(`Detected ${this.failedSinkWrites} failed sink writes.`);
    }

    return freezeDeepSafe({
      runtimeState: this.lifecycleState,
      loggerCount: this.registry.getLoggerCount(),
      sinkCount: this.sinks.size,
      historySize: this.history.length,
      statistics: this.getStatistics(),
      generatedAt: Date.now(),
      warnings
    });
  }
}
