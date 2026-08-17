export interface AlertingTelemetryStatistics {
  readonly totalIntegrationAttempts: number;
  readonly successfulIntegrations: number;
  readonly skippedIntegrations: number;
  readonly duplicateEvents: number;
  readonly rejectedEvents: number;
  readonly failedIntegrations: number;
  readonly telemetryRecordsCreated: number;
  readonly telemetryDispatchFailures: number;
  readonly policyMatches: number;
  readonly policyMisses: number;
  readonly averageIntegrationDuration: number;
  readonly batchCount: number;
  readonly batchItemCount: number;
}
