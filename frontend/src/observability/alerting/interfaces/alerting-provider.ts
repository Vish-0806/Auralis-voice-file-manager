import { AlertRule } from '../models/rule';
import { AlertRecord } from '../models/alert';
import { AlertEvaluationResult } from '../models/evaluation';
import { AlertStatistics } from '../models/statistics';

export interface IAlertingProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;

  registerRule(rule: AlertRule): void;
  unregisterRule(ruleId: string): void;
  getRule(ruleId: string): AlertRule | null;
  hasRule(ruleId: string): boolean;
  listRules(): ReadonlyArray<AlertRule>;

  evaluate(context: Record<string, unknown> | ReadonlyArray<Record<string, unknown>>): Promise<ReadonlyArray<AlertEvaluationResult>>;

  suppressAlert(alertId: string, durationMs: number): AlertRecord;
  resumeAlert(alertId: string): AlertRecord;
  acknowledgeAlert(alertId: string, acknowledgedBy: string): AlertRecord;
  resolveAlert(alertId: string, resolvedBy?: string): AlertRecord;

  getAlert(alertId: string): AlertRecord | null;
  listActiveAlerts(): ReadonlyArray<AlertRecord>;
  listAlerts(): ReadonlyArray<AlertRecord>;
  findByFingerprint(fingerprint: string): AlertRecord | null;

  getHistory(): ReadonlyArray<AlertRecord>;
  clearHistory(): void;

  getStatistics(): AlertStatistics;
  getDiagnostics(): {
    readonly runtimeState: string;
    readonly ruleCount: number;
    readonly enabledRuleCount: number;
    readonly activeAlertCount: number;
    readonly historySize: number;
    readonly statistics: AlertStatistics;
    readonly generatedAt: number;
  };
}
