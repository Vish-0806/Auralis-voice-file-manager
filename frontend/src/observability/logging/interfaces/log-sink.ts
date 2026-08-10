import type { LogRecord, LogLevelValue } from '../models/log';
import type { LogSinkStatistics } from '../models/sink';

export interface ILogSink {
  readonly id: string;
  readonly name: string;
  isEnabled(): boolean;
  setEnabled(enabled: boolean): void;
  getMinLevel(): LogLevelValue;
  setMinLevel(level: LogLevelValue): void;
  write(record: LogRecord): Promise<void>;
  flush(): Promise<void>;
  close(): Promise<void>;
  getStatistics(): LogSinkStatistics;
}
