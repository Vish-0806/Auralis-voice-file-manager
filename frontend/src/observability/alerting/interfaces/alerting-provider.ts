import type { AlertRecord } from '../models/alert';
import type { AlertRule } from '../models/alert-rule';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import type { AlertingRuntimeStateValue } from '../models/runtime';
import type { AlertEvaluationContext, RuleEvaluationResult } from '../models/evaluation';

export interface IAlertingProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getRuntimeState(): AlertingRuntimeStateValue;
  getState(): AlertingRuntimeStateValue; // for backwards/system-wide state checking compatibility

  registerAlert(alert: AlertRecord): void;
  getAlert(alertId: string): AlertRecord | null;
  hasAlert(alertId: string): boolean;
  removeAlert(alertId: string): void;
  listAlerts(): ReadonlyArray<AlertRecord>;
  clearAlerts(): void;

  registerRule(rule: AlertRule): void;
  unregisterRule(ruleId: string): void;
  getRule(ruleId: string): AlertRule | null;
  hasRule(ruleId: string): boolean;
  listRules(): ReadonlyArray<AlertRule>;
  updateRule(rule: AlertRule): void;
  clearRules(): void;

  evaluateRule(rule: AlertRule, context: AlertEvaluationContext): RuleEvaluationResult;
  generateAlert(rule: AlertRule, evaluationResult: RuleEvaluationResult): AlertRecord;

  getStatistics(): AlertingStatistics;
  getDiagnostics(): AlertingDiagnostics;
}