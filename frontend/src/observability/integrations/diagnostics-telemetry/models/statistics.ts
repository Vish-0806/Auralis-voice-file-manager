export interface DiagnosticsTelemetryStatistics {
  readonly totalEvaluations: number;
  readonly matchedPolicies: number;
  readonly skippedResults: number;
  readonly acceptedResults: number;
  readonly rejectedResults: number;
  readonly telemetryRecordsEmitted: number;
  readonly sampledRecords: number;
  readonly unsampledRecords: number;
  readonly severityBypasses: number;
  readonly duplicateEvents: number;
  readonly failedIntegrations: number;
  readonly averageProcessingDuration: number;
  readonly runLevelIntegrations: number;
  readonly resultLevelIntegrations: number;
}
