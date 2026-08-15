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

  // Extended for Phase 18.7.4
  readonly totalAlertGenerations: number;
  readonly successfulAlertGenerations: number;
  readonly rejectedAlertGenerations: number;
  readonly generationErrors: number;
  readonly totalGenerationDuration: number;
  readonly averageGenerationDuration: number;
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

  // Extended for Phase 18.7.4
  readonly totalAlertGenerations: number;
  readonly successfulAlertGenerations: number;
  readonly rejectedAlertGenerations: number;
  readonly generationErrors: number;
  readonly totalGenerationDuration: number;
  readonly averageGenerationDuration: number;

  readonly generatedAt: number;
}