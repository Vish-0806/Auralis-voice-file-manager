export interface MonitoringAlertIntegrationStatistics {
  readonly evaluations: number;
  readonly matchedPolicies: number;
  readonly skippedTriggers: number;
  readonly alertingRequests: number;
  readonly successfulAlertingRequests: number;
  readonly failedAlertingRequests: number;
  readonly suppressedRequests: number;
  readonly deduplicatedRequests: number;
  readonly duplicateIntegrationRequests: number;
  readonly integrationErrors: number;
  readonly averageIntegrationDuration: number;
}
