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
  readonly generatedAt: number;
}