export interface LogSinkStatistics {
  readonly totalWrites: number;
  readonly failedWrites: number;
  readonly lastWriteTimestamp?: number;
}
