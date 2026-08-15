import type { AlertRuleStatistics } from './rule-statistics';

export interface AlertingStatistics extends AlertRuleStatistics {
  readonly registeredAlertCount: number;
  readonly totalEvaluations: number;
  readonly matchedEvaluations: number;
  readonly unmatchedEvaluations: number;
  readonly errorEvaluations: number;
  readonly skippedEvaluations: number;
  readonly totalEvaluationDuration: number;
  readonly averageEvaluationDuration: number;

  readonly totalAlertGenerations: number;
  readonly successfulAlertGenerations: number;
  readonly rejectedAlertGenerations: number;
  readonly generationErrors: number;
  readonly totalGenerationDuration: number;
  readonly averageGenerationDuration: number;

  // Extended for Phase 18.7.5
  readonly totalDeduplicationChecks: number;
  readonly acceptedAlertCount: number;
  readonly duplicateAlertCount: number;
  readonly cooldownSuppressedCount: number;
  readonly activeCooldownCount: number;
  readonly trackedFingerprintCount: number;
}

export interface AlertingDiagnostics extends AlertRuleStatistics {
  readonly runtimeState: string;
  readonly registeredAlertCount: number;
  readonly totalEvaluations: number;
  readonly matchedEvaluations: number;
  readonly unmatchedEvaluations: number;
  readonly errorEvaluations: number;
  readonly skippedEvaluations: number;
  readonly totalEvaluationDuration: number;
  readonly averageEvaluationDuration: number;

  readonly totalAlertGenerations: number;
  readonly successfulAlertGenerations: number;
  readonly rejectedAlertGenerations: number;
  readonly generationErrors: number;
  readonly totalGenerationDuration: number;
  readonly averageGenerationDuration: number;

  // Extended for Phase 18.7.5
  readonly totalDeduplicationChecks: number;
  readonly acceptedAlertCount: number;
  readonly duplicateAlertCount: number;
  readonly cooldownSuppressedCount: number;
  readonly activeCooldownCount: number;
  readonly trackedFingerprintCount: number;

  readonly generatedAt: number;
}