export interface LoggingStatistics {
  readonly totalRecords: number;
  readonly traceCount: number;
  readonly debugCount: number;
  readonly infoCount: number;
  readonly warnCount: number;
  readonly errorCount: number;
  readonly fatalCount: number;
  readonly filteredCount: number;
  readonly dispatchedCount: number;
  readonly failedSinkWrites: number;
  readonly registeredLoggerCount: number;
  readonly registeredSinkCount: number;
  readonly lastLogTimestamp?: number;
}

export interface LoggingDiagnostics {
  readonly runtimeState: string;
  readonly loggerCount: number;
  readonly sinkCount: number;
  readonly historySize: number;
  readonly statistics: LoggingStatistics;
  readonly generatedAt: number;
  readonly warnings: ReadonlyArray<string>;
}
