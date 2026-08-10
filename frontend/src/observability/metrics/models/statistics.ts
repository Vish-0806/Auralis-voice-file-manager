export interface MetricsStatistics {
  readonly registeredMetricCount: number;
  readonly totalSamples: number;
  readonly counterSamples: number;
  readonly gaugeSamples: number;
  readonly histogramSamples: number;
  readonly timerSamples: number;
  readonly rejectedSamples: number;
  readonly historySize: number;
  readonly lastSampleTimestamp?: number;
  readonly minSampleValue?: number;
  readonly maxSampleValue?: number;
}

export interface MetricsDiagnostics {
  readonly runtimeState: string;
  readonly metricCount: number;
  readonly seriesCount: number;
  readonly historySize: number;
  readonly statistics: MetricsStatistics;
  readonly generatedAt: number;
  readonly warnings: ReadonlyArray<string>;
}
