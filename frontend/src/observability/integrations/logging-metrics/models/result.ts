export interface LoggingMetricResult {
  readonly status: 'ACCEPTED' | 'SKIPPED' | 'REJECTED';
  readonly triggerId?: string;
  readonly metricName?: string;
  readonly operation?: string;
  readonly reason?: string;
  readonly duration: number;
  readonly timestamp: number;
}
