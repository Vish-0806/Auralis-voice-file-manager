import type { IAlertingRuntime } from '../interfaces/alerting-runtime';
import type { IAlertingProvider } from '../interfaces/alerting-provider';
import { AlertingProvider } from '../provider/AlertingProvider';
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
import type { INotificationChannel } from '../interfaces/notification-channel';
import type { NotificationRequest, NotificationDeliveryResult } from '../models/notification';

export class AlertingRuntime implements IAlertingRuntime {
  private readonly _provider: IAlertingProvider;

  constructor(provider?: IAlertingProvider) {
    this._provider = provider || new AlertingProvider();
  }

  public provider(): IAlertingProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getRuntimeState(): AlertingRuntimeStateValue {
    return this._provider.getRuntimeState();
  }

  public getState(): AlertingRuntimeStateValue {
    return this._provider.getState();
  }

  // --- Alert API ---
  public registerAlert(alert: AlertRecord): void {
    this._provider.registerAlert(alert);
  }

  public getAlert(alertId: string): AlertRecord | null {
    return this._provider.getAlert(alertId);
  }

  public hasAlert(alertId: string): boolean {
    return this._provider.hasAlert(alertId);
  }

  public removeAlert(alertId: string): void {
    this._provider.removeAlert(alertId);
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    return this._provider.listAlerts();
  }

  public clearAlerts(): void {
    this._provider.clearAlerts();
  }

  // --- Rule API ---
  public registerRule(rule: AlertRule): void {
    this._provider.registerRule(rule);
  }

  public unregisterRule(ruleId: string): void {
    this._provider.unregisterRule(ruleId);
  }

  public getRule(ruleId: string): AlertRule | null {
    return this._provider.getRule(ruleId);
  }

  public hasRule(ruleId: string): boolean {
    return this._provider.hasRule(ruleId);
  }

  public listRules(): ReadonlyArray<AlertRule> {
    return this._provider.listRules();
  }

  public updateRule(rule: AlertRule): void {
    this._provider.updateRule(rule);
  }

  public clearRules(): void {
    this._provider.clearRules();
  }

  // --- Evaluation API ---
  public evaluateRule(rule: AlertRule, context: AlertEvaluationContext): RuleEvaluationResult {
    return this._provider.evaluateRule(rule, context);
  }

  // --- Generation API ---
  public generateAlert(rule: AlertRule, evaluationResult: RuleEvaluationResult): AlertRecord {
    return this._provider.generateAlert(rule, evaluationResult);
  }

  // --- Deduplication API ---
  public checkDeduplication(alert: AlertRecord, now?: number): DeduplicationDecision {
    return this._provider.checkDeduplication(alert, now);
  }

  public getDeduplicationRecord(identityKey: string): DeduplicationRecord | null {
    return this._provider.getDeduplicationRecord(identityKey);
  }

  public clearDeduplication(): void {
    this._provider.clearDeduplication();
  }

  // --- Lifecycle API ---
  public initializeAlertLifecycle(alertId: string, fingerprint?: string, now?: number): AlertLifecycleRecord {
    return this._provider.initializeAlertLifecycle(alertId, fingerprint, now);
  }

  public getAlertLifecycle(alertId: string): AlertLifecycleRecord | null {
    return this._provider.getAlertLifecycle(alertId);
  }

  public acknowledgeAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord {
    return this._provider.acknowledgeAlert(alertId, actor, reason, metadata, now);
  }

  public resolveAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord {
    return this._provider.resolveAlert(alertId, actor, reason, metadata, now);
  }

  public closeAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord {
    return this._provider.closeAlert(alertId, actor, reason, metadata, now);
  }

  public getAlertLifecycleHistory(alertId: string): ReadonlyArray<AlertLifecycleHistoryEntry> {
    return this._provider.getAlertLifecycleHistory(alertId);
  }

  // --- Suppression API ---
  public registerSuppressionPolicy(policy: AlertSuppressionPolicy): void {
    this._provider.registerSuppressionPolicy(policy);
  }

  public unregisterSuppressionPolicy(policyId: string): void {
    this._provider.unregisterSuppressionPolicy(policyId);
  }

  public listSuppressionPolicies(): ReadonlyArray<AlertSuppressionPolicy> {
    return this._provider.listSuppressionPolicies();
  }

  public registerMaintenanceWindow(window: AlertMaintenanceWindow): void {
    this._provider.registerMaintenanceWindow(window);
  }

  public unregisterMaintenanceWindow(windowId: string): void {
    this._provider.unregisterMaintenanceWindow(windowId);
  }

  public listMaintenanceWindows(): ReadonlyArray<AlertMaintenanceWindow> {
    return this._provider.listMaintenanceWindows();
  }

  public snoozeAlert(
    alertId: string,
    fingerprint: string | undefined,
    durationMs: number,
    actor: string,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertSnoozeRecord {
    return this._provider.snoozeAlert(alertId, fingerprint, durationMs, actor, reason, metadata, now);
  }

  public clearSnooze(alertId: string): void {
    this._provider.clearSnooze(alertId);
  }

  public getSnooze(alertId: string): AlertSnoozeRecord | null {
    return this._provider.getSnooze(alertId);
  }

  public evaluateSuppression(alert: AlertRecord, now?: number): AlertSuppressionDecision {
    return this._provider.evaluateSuppression(alert, now);
  }

  // --- Notification API ---
  public registerNotificationChannel(channel: INotificationChannel): void {
    this._provider.registerNotificationChannel(channel);
  }

  public unregisterNotificationChannel(channelId: string): void {
    this._provider.unregisterNotificationChannel(channelId);
  }

  public getNotificationChannel(channelId: string): INotificationChannel | null {
    return this._provider.getNotificationChannel(channelId);
  }

  public listNotificationChannels(): ReadonlyArray<INotificationChannel> {
    return this._provider.listNotificationChannels();
  }

  public enableNotificationChannel(channelId: string): void {
    this._provider.enableNotificationChannel(channelId);
  }

  public disableNotificationChannel(channelId: string): void {
    this._provider.disableNotificationChannel(channelId);
  }

  public dispatchNotification(request: NotificationRequest, maxAttempts?: number): Promise<NotificationDeliveryResult> {
    return this._provider.dispatchNotification(request, maxAttempts);
  }

  public getNotificationDeliveryHistory(): ReadonlyArray<NotificationDeliveryResult> {
    return this._provider.getNotificationDeliveryHistory();
  }

  // --- Stats & Diags ---
  public getStatistics(): AlertingStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): AlertingDiagnostics {
    return this._provider.getDiagnostics();
  }
}
