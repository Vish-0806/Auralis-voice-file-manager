export interface DiagnosticsStatistics {
  readonly totalRuns: number;
  readonly successfulRuns: number;
  readonly degradedRuns: number;
  readonly failedRuns: number; // failed/unhealthy runs
  readonly skippedChecks: number;
  readonly executedChecks: number;
  readonly failedChecks: number;
  readonly timedOutChecks: number;
  readonly totalDuration: number;
  readonly averageDuration: number;
  readonly sourceCount: number;
  readonly checkCount: number;
}
