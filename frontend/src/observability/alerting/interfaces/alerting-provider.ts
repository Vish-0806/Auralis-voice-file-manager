import type { AlertRecord } from '../models/alert';
import type { AlertRule } from '../models/alert-rule';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import type { AlertingRuntimeStateValue } from '../models/runtime';
import type { AlertEvaluationContext, RuleEvaluationResult } from '../models/evaluation';
import type { DeduplicationDecision, DeduplicationRecord } from '../models/deduplication';
import type { AlertLifecycleRecord, AlertLifecycleHistoryEntry, AlertLifecycleActorValue } from '../models/lifecycle';
import type {
  AlertSuppressionPolicy,
  AlertMaintenanceWindow,
  AlertSnoozeRecord,
  AlertSuppressionDecision
} from '../models/suppression';
import type { INotificationChannel } from './notification-channel';
import type { NotificationRequest, NotificationDeliveryResult } from '../models/notification';
import type { IAlertOrchestrationManager } from './alert-orchestration';
import type { IAlertCertificationManager } from './alert-certification';

export interface IAlertingProvider extends IAlertOrchestrationManager, IAlertCertificationManager {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getRuntimeState(): AlertingRuntimeStateValue;
  getState(): AlertingRuntimeStateValue;

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

  checkDeduplication(alert: AlertRecord, now?: number): DeduplicationDecision;
  getDeduplicationRecord(identityKey: string): DeduplicationRecord | null;
  clearDeduplication(): void;

  initializeAlertLifecycle(alertId: string, fingerprint?: string, now?: number): AlertLifecycleRecord;
  getAlertLifecycle(alertId: string): AlertLifecycleRecord | null;
  acknowledgeAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord;
  resolveAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord;
  closeAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord;
  getAlertLifecycleHistory(alertId: string): ReadonlyArray<AlertLifecycleHistoryEntry>;

  registerSuppressionPolicy(policy: AlertSuppressionPolicy): void;
  unregisterSuppressionPolicy(policyId: string): void;
  listSuppressionPolicies(): ReadonlyArray<AlertSuppressionPolicy>;
  registerMaintenanceWindow(window: AlertMaintenanceWindow): void;
  unregisterMaintenanceWindow(windowId: string): void;
  listMaintenanceWindows(): ReadonlyArray<AlertMaintenanceWindow>;
  snoozeAlert(
    alertId: string,
    fingerprint: string | undefined,
    durationMs: number,
    actor: string,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertSnoozeRecord;
  clearSnooze(alertId: string): void;
  getSnooze(alertId: string): AlertSnoozeRecord | null;
  evaluateSuppression(alert: AlertRecord, now?: number): AlertSuppressionDecision;

  registerNotificationChannel(channel: INotificationChannel): void;
  unregisterNotificationChannel(channelId: string): void;
  getNotificationChannel(channelId: string): INotificationChannel | null;
  listNotificationChannels(): ReadonlyArray<INotificationChannel>;
  enableNotificationChannel(channelId: string): void;
  disableNotificationChannel(channelId: string): void;
  dispatchNotification(request: NotificationRequest, maxAttempts?: number): Promise<NotificationDeliveryResult>;
  getNotificationDeliveryHistory(): ReadonlyArray<NotificationDeliveryResult>;

  getStatistics(): AlertingStatistics;
  getDiagnostics(): AlertingDiagnostics;
}