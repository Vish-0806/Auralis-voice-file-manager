export interface ObservabilityCompositionStatistics {
  readonly initializationCount: number;
  readonly shutdownCount: number;
  readonly initializationFailures: number;
  readonly shutdownFailures: number;
  readonly totalLifecycleOperations: number;
  readonly successfulLifecycleOperations: number;
  readonly failedLifecycleOperations: number;
  readonly averageLifecycleDurationMs: number;
}
