export interface TracingTelemetryStatistics {
  readonly totalEvaluations: number;
  readonly matchedPolicies: number;
  readonly skippedSpans: number;
  readonly acceptedSpans: number;
  readonly rejectedSpans: number;
  readonly telemetryRecordsEmitted: number;
  readonly sampledRecords: number;
  readonly unsampledRecords: number;
  readonly errorBypasses: number;
  readonly duplicateEvents: number;
  readonly failedIntegrations: number;
  readonly averageProcessingDuration: number;
}
