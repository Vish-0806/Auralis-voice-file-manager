import type { AlertRuleStatistics } from './rule-statistics';

export interface AlertingStatistics extends AlertRuleStatistics {
  readonly registeredAlertCount: number;
}

export interface AlertingDiagnostics extends AlertRuleStatistics {
  readonly runtimeState: string;
  readonly registeredAlertCount: number;
  readonly generatedAt: number;
}