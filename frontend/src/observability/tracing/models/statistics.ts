export interface TracingStatistics {
  readonly traceCount: number;
  readonly spanCount: number;
  readonly activeSpanCount: number;
  readonly completedSpanCount: number;
  readonly errorSpanCount: number;
  readonly averageDuration: number;
  readonly totalDuration: number;
  readonly maximumDuration: number;
  readonly minimumDuration: number;
  readonly eventCount: number;
}

export interface TracingDiagnostics {
  readonly runtimeState: string;
  readonly traceCount: number;
  readonly activeSpanCount: number;
  readonly completedSpanCount: number;
  readonly statistics: TracingStatistics;
  readonly historyCapacity: number;
  readonly generatedAt: number;
}
