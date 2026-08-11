export interface AlertStatistics {
  readonly totalEvaluations: number;
  readonly matchedRules: number;
  readonly unmatchedRules: number;
  readonly alertsCreated: number;
  readonly alertsDeduplicated: number;
  readonly alertsAcknowledged: number;
  readonly alertsSuppressed: number;
  readonly alertsResumed: number;
  readonly alertsResolved: number;
  readonly alertsExpired: number;
  readonly evaluationFailures: number;
  readonly totalEvaluationDuration: number;
  readonly averageEvaluationDuration: number;
  readonly activeAlertCount: number;
  readonly registeredRuleCount: number;
}
