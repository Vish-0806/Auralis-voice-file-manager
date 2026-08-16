export interface LoggingMetricsStatistics {
  readonly totalEvaluations: number;
  readonly matchedPolicies: number;
  readonly skippedEvents: number;
  readonly acceptedEvents: number;
  readonly rejectedEvents: number;
  readonly metricObservationsEmitted: number;
  readonly counterIncrements: number;
  readonly gaugeUpdates: number;
  readonly histogramObservations: number;
  readonly timerObservations: number;
  readonly failedIntegrations: number;
  readonly averageProcessingDuration: number;
}
