import type { ILogSink } from '../interfaces/log-sink';
import { type LogRecord, type LogLevelValue, LogLevel } from '../models/log';
import type { LogSinkStatistics } from '../models/sink';
import { LoggingValidationError } from '../errors/LoggingErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class InMemoryLogSink implements ILogSink {
  private enabled = true;
  private minLevel: LogLevelValue = LogLevel.TRACE;
  private records: LogRecord[] = [];
  
  private totalWrites = 0;
  private failedWrites = 0;
  private lastWriteTimestamp?: number;

  constructor(
    public readonly id: string,
    public readonly name: string,
    private readonly capacity: number = 1000
  ) {
    if (!id || !id.trim()) {
      throw new LoggingValidationError('Sink ID cannot be empty.');
    }
    if (!name || !name.trim()) {
      throw new LoggingValidationError('Sink name cannot be empty.');
    }
    if (typeof capacity !== 'number' || capacity <= 0 || !Number.isInteger(capacity)) {
      throw new LoggingValidationError('Capacity must be an integer greater than 0.');
    }
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  public getMinLevel(): LogLevelValue {
    return this.minLevel;
  }

  public setMinLevel(level: LogLevelValue): void {
    if (!Object.values(LogLevel).includes(level)) {
      throw new LoggingValidationError(`Invalid log level: ${level}`);
    }
    this.minLevel = level;
  }

  public async write(record: LogRecord): Promise<void> {
    if (!this.enabled) {
      return;
    }
    
    try {
      this.totalWrites += 1;
      this.lastWriteTimestamp = Date.now();

      if (this.records.length >= this.capacity) {
        this.records.shift();
      }

      this.records.push(record);
    } catch (err) {
      this.failedWrites += 1;
      throw err;
    }
  }

  public async flush(): Promise<void> {
    // In-memory flush is a no-op
  }

  public async close(): Promise<void> {
    this.enabled = false;
  }

  public getRecords(): ReadonlyArray<LogRecord> {
    return freezeDeepSafe(this.records) as ReadonlyArray<LogRecord>;
  }

  public getRecordCount(): number {
    return this.records.length;
  }

  public clear(): void {
    this.records = [];
  }

  public getStatistics(): LogSinkStatistics {
    return freezeDeepSafe({
      totalWrites: this.totalWrites,
      failedWrites: this.failedWrites,
      lastWriteTimestamp: this.lastWriteTimestamp
    });
  }
}
