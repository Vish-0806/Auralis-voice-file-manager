import type { IAlertingProvider } from '../interfaces/alerting-provider';
import type { AlertRecord } from '../models/alert';
import type { AlertRule } from '../models/alert-rule';
import { AlertingRuntimeState, AlertingRuntimeStateValue } from '../models/runtime';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import type { AlertEvaluationContext, RuleEvaluationResult } from '../models/evaluation';
import type { DeduplicationDecision, DeduplicationRecord, DeduplicationPolicy } from '../models/deduplication';
import type { AlertLifecycleRecord, AlertLifecycleHistoryEntry, AlertLifecycleActorValue } from '../models/lifecycle';
import type {
  AlertSuppressionPolicy,
  AlertMaintenanceWindow,
  AlertSnoozeRecord,
  AlertSuppressionDecision
} from '../models/suppression';
import type { INotificationChannel } from '../interfaces/notification-channel';
import type { NotificationRequest, NotificationDeliveryResult } from '../models/notification';
import type { AlertOrchestrationRequest, AlertOrchestrationResult } from '../models/orchestration';
import { AlertRegistry } from '../registry/AlertRegistry';
import { AlertEvaluator } from '../evaluator/AlertEvaluator';
import { AlertGenerator } from '../generator/AlertGenerator';
import { AlertDeduplicator } from '../deduplication/AlertDeduplicator';
import { AlertLifecycleManager } from '../lifecycle/AlertLifecycleManager';
import { AlertSuppressionManager } from '../suppression/AlertSuppressionManager';
import { NotificationChannelRegistry } from '../notifications/NotificationChannelRegistry';
import { NotificationDispatcher } from '../notifications/NotificationDispatcher';
import { AlertOrchestrator } from '../orchestration/AlertOrchestrator';
import { AlertingStateError, AlertGenerationError } from '../errors/AlertingErrors';
import { createAlertingStatistics, createAlertingDiagnostics } from '../factories/alertingFactories';
import { AlertCertifier } from '../certification/AlertCertifier';
import {
  AlertCertificationStageValue,
  AlertCertificationStageResult,
  AlertCertificationReport
} from '../models/certification';

export class AlertingProvider implements IAlertingProvider {
  private _state: AlertingRuntimeStateValue = AlertingRuntimeState.UNINITIALIZED;
  private readonly _registry = new AlertRegistry();
  private readonly _evaluator = new AlertEvaluator();
  private readonly _generator = new AlertGenerator();
  private readonly _deduplicator = new AlertDeduplicator();
  private readonly _lifecycleManager = new AlertLifecycleManager();
  private readonly _suppressionManager = new AlertSuppressionManager();
  private readonly _notificationRegistry = new NotificationChannelRegistry();
  private readonly _notificationDispatcher: NotificationDispatcher;
  private readonly _orchestrator: AlertOrchestrator;
  private readonly _certifier = new AlertCertifier();

  private readonly _policy: DeduplicationPolicy = {
    enabled: true,
    cooldownMs: 5000,
    scope: 'PER_RULE',
    maxHistorySize: 1000
  };

  // Evaluation counters
  private _totalEvaluations = 0;
  private _matchedEvaluations = 0;
  private _unmatchedEvaluations = 0;
  private _errorEvaluations = 0;
  private _skippedEvaluations = 0;
  private _totalEvaluationDuration = 0;

  // Generation counters
  private _totalAlertGenerations = 0;
  private _successfulAlertGenerations = 0;
  private _rejectedAlertGenerations = 0;
  private _generationErrors = 0;
  private _totalGenerationDuration = 0;

  // Deduplication counters
  private _totalDeduplicationChecks = 0;
  private _acceptedAlertCount = 0;
  private _duplicateAlertCount = 0;
  private _cooldownSuppressedCount = 0;

  constructor() {
    this._notificationDispatcher = new NotificationDispatcher(this._notificationRegistry);
    this._orchestrator = new AlertOrchestrator(this);
  }

  private ensureReady(action: string): void {
    if (this._state !== AlertingRuntimeState.READY) {
      throw new AlertingStateError(
        `Cannot perform action '${action}' when state is ${this._state}. Provider must be READY.`
      );
    }
  }

  public async initialize(): Promise<void> {
    if (this._state === AlertingRuntimeState.READY) {
      return;
    }
    if (
      this._state === AlertingRuntimeState.INITIALIZING ||
      this._state === AlertingRuntimeState.STOPPING ||
      this._state === AlertingRuntimeState.STOPPED
    ) {
      throw new AlertingStateError(`Cannot initialize alerting provider from state: ${this._state}`);
    }

    this._state = AlertingRuntimeState.INITIALIZING;
    try {
      this._state = AlertingRuntimeState.READY;
    } catch (err: any) {
      this._state = AlertingRuntimeState.ERROR;
      throw err;
    }
  }

  public async shutdown(): Promise<void> {
    if (this._state === AlertingRuntimeState.STOPPED) {
      return;
    }
    if (this._state === AlertingRuntimeState.UNINITIALIZED) {
      throw new AlertingStateError('Cannot shutdown alerting provider: it is not initialized.');
    }

    this._state = AlertingRuntimeState.STOPPING;
    try {
      this._registry.clear();
      this._registry.clearRules();
      this._deduplicator.clear();
      this._lifecycleManager.clearAll();
      this._suppressionManager.clearAll();
      this._notificationRegistry.clear();
      this._notificationDispatcher.clear();
      this._orchestrator.clear();
      this._certifier.reset();
      this.clearEvaluationStats();
      this.clearGenerationStats();
      this.clearDeduplicationStats();
    } finally {
      this._state = AlertingRuntimeState.STOPPED;
    }
  }

  public getRuntimeState(): AlertingRuntimeStateValue {
    return this._state;
  }

  public getState(): AlertingRuntimeStateValue {
    return this._state;
  }

  // --- Alert API ---
  public registerAlert(alert: AlertRecord): void {
    this.ensureReady('registerAlert');
    this._registry.registerAlert(alert);
    this._lifecycleManager.initializeRecord(alert.id, alert.fingerprint, alert.triggeredAt || alert.generatedAt || Date.now());
  }

  public getAlert(alertId: string): AlertRecord | null {
    this.ensureReady('getAlert');
    return this._registry.getAlert(alertId);
  }

  public hasAlert(alertId: string): boolean {
    this.ensureReady('hasAlert');
    return this._registry.hasAlert(alertId);
  }

  public removeAlert(alertId: string): void {
    this.ensureReady('removeAlert');
    this._registry.removeAlert(alertId);
    this._lifecycleManager.clear(alertId);
    this._suppressionManager.clearSnooze(alertId);
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    this.ensureReady('listAlerts');
    return this._registry.listAlerts();
  }

  public clearAlerts(): void {
    this.ensureReady('clearAlerts');
    this._registry.clear();
    this._lifecycleManager.clearAll();
    this._suppressionManager.clearAll();
  }

  // --- Rule API ---
  public registerRule(rule: AlertRule): void {
    this.ensureReady('registerRule');
    this._registry.registerRule(rule);
  }

  public unregisterRule(ruleId: string): void {
    this.ensureReady('unregisterRule');
    this._registry.unregisterRule(ruleId);
  }

  public getRule(ruleId: string): AlertRule | null {
    this.ensureReady('getRule');
    return this._registry.getRule(ruleId);
  }

  public hasRule(ruleId: string): boolean {
    this.ensureReady('hasRule');
    return this._registry.hasRule(ruleId);
  }

  public listRules(): ReadonlyArray<AlertRule> {
    this.ensureReady('listRules');
    return this._registry.listRules();
  }

  public updateRule(rule: AlertRule): void {
    this.ensureReady('updateRule');
    this._registry.updateRule(rule);
  }

  public clearRules(): void {
    this.ensureReady('clearRules');
    this._registry.clearRules();
  }

  // --- Evaluation API ---
  public evaluateRule(rule: AlertRule, context: AlertEvaluationContext): RuleEvaluationResult {
    this.ensureReady('evaluateRule');
    const result = this._evaluator.evaluateRule(rule, context);

    this._totalEvaluations++;
    this._totalEvaluationDuration += result.durationMs;

    if (result.status === 'SKIPPED') {
      this._skippedEvaluations++;
    } else if (result.status === 'ERROR') {
      this._errorEvaluations++;
    } else if (result.status === 'MATCHED') {
      this._matchedEvaluations++;
    } else if (result.status === 'NOT_MATCHED') {
      this._unmatchedEvaluations++;
    }

    return result;
  }

  // --- Generation API ---
  public generateAlert(rule: AlertRule, evaluationResult: RuleEvaluationResult): AlertRecord {
    this.ensureReady('generateAlert');
    const startTime = performance.now();
    this._totalAlertGenerations++;

    try {
      const alert = this._generator.generate(rule, evaluationResult);

      this._registry.registerAlert(alert);

      const generatedAt = alert.generatedAt || Date.now();
      this._lifecycleManager.initializeRecord(alert.id, alert.fingerprint, generatedAt);

      this._successfulAlertGenerations++;
      const duration = performance.now() - startTime;
      this._totalGenerationDuration += duration;
      return alert;
    } catch (err: any) {
      const duration = performance.now() - startTime;
      this._totalGenerationDuration += duration;

      if (err instanceof AlertGenerationError) {
        this._rejectedAlertGenerations++;
      } else {
        this._generationErrors++;
      }
      throw err;
    }
  }

  // --- Deduplication API ---
  public checkDeduplication(alert: AlertRecord, now?: number): DeduplicationDecision {
    this.ensureReady('checkDeduplication');
    const timestamp = now !== undefined ? now : Date.now();
    const decision = this._deduplicator.check(alert, this._policy, timestamp);

    this._totalDeduplicationChecks++;
    if (decision.decision === 'ACCEPTED') {
      this._acceptedAlertCount++;
    } else if (decision.decision === 'DUPLICATE') {
      this._duplicateAlertCount++;
    } else if (decision.decision === 'COOLDOWN_SUPPRESSED') {
      this._cooldownSuppressedCount++;
      this._duplicateAlertCount++;
    }

    return decision;
  }

  public getDeduplicationRecord(identityKey: string): DeduplicationRecord | null {
    this.ensureReady('getDeduplicationRecord');
    return this._deduplicator.getRecord(identityKey);
  }

  public clearDeduplication(): void {
    this.ensureReady('clearDeduplication');
    this._deduplicator.clear();
  }

  // --- Lifecycle API ---
  public initializeAlertLifecycle(alertId: string, fingerprint?: string, now?: number): AlertLifecycleRecord {
    this.ensureReady('initializeAlertLifecycle');
    return this._lifecycleManager.initializeRecord(alertId, fingerprint, now);
  }

  public getAlertLifecycle(alertId: string): AlertLifecycleRecord | null {
    this.ensureReady('getAlertLifecycle');
    return this._lifecycleManager.getRecord(alertId);
  }

  public acknowledgeAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord {
    this.ensureReady('acknowledgeAlert');
    return this._lifecycleManager.transition(alertId, 'ACKNOWLEDGED', actor, 'ACKNOWLEDGE', reason, metadata, now);
  }

  public resolveAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord {
    this.ensureReady('resolveAlert');
    return this._lifecycleManager.transition(alertId, 'RESOLVED', actor, 'RESOLVE', reason, metadata, now);
  }

  public closeAlert(
    alertId: string,
    actor: AlertLifecycleActorValue,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord {
    this.ensureReady('closeAlert');
    return this._lifecycleManager.transition(alertId, 'CLOSED', actor, 'CLOSE', reason, metadata, now);
  }

  public getAlertLifecycleHistory(alertId: string): ReadonlyArray<AlertLifecycleHistoryEntry> {
    this.ensureReady('getAlertLifecycleHistory');
    return this._lifecycleManager.getHistory(alertId);
  }

  // --- Suppression API ---
  public registerSuppressionPolicy(policy: AlertSuppressionPolicy): void {
    this.ensureReady('registerSuppressionPolicy');
    this._suppressionManager.registerPolicy(policy);
  }

  public unregisterSuppressionPolicy(policyId: string): void {
    this.ensureReady('unregisterSuppressionPolicy');
    this._suppressionManager.unregisterPolicy(policyId);
  }

  public listSuppressionPolicies(): ReadonlyArray<AlertSuppressionPolicy> {
    this.ensureReady('listSuppressionPolicies');
    return this._suppressionManager.listPolicies();
  }

  public registerMaintenanceWindow(window: AlertMaintenanceWindow): void {
    this.ensureReady('registerMaintenanceWindow');
    this._suppressionManager.registerMaintenanceWindow(window);
  }

  public unregisterMaintenanceWindow(windowId: string): void {
    this.ensureReady('unregisterMaintenanceWindow');
    this._suppressionManager.unregisterMaintenanceWindow(windowId);
  }

  public listMaintenanceWindows(): ReadonlyArray<AlertMaintenanceWindow> {
    this.ensureReady('listMaintenanceWindows');
    return this._suppressionManager.listMaintenanceWindows();
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
    this.ensureReady('snoozeAlert');
    return this._suppressionManager.snoozeAlert(alertId, fingerprint, durationMs, actor, reason, metadata, now);
  }

  public clearSnooze(alertId: string): void {
    this.ensureReady('clearSnooze');
    this._suppressionManager.clearSnooze(alertId);
  }

  public getSnooze(alertId: string): AlertSnoozeRecord | null {
    this.ensureReady('getSnooze');
    return this._suppressionManager.getSnooze(alertId);
  }

  public evaluateSuppression(alert: AlertRecord, now?: number): AlertSuppressionDecision {
    this.ensureReady('evaluateSuppression');
    return this._suppressionManager.evaluateSuppression(alert, now);
  }

  // --- Notification Channel Runtime APIs ---
  public registerNotificationChannel(channel: INotificationChannel): void {
    this.ensureReady('registerNotificationChannel');
    this._notificationRegistry.register(channel);
  }

  public unregisterNotificationChannel(channelId: string): void {
    this.ensureReady('unregisterNotificationChannel');
    this._notificationRegistry.unregister(channelId);
  }

  public getNotificationChannel(channelId: string): INotificationChannel | null {
    this.ensureReady('getNotificationChannel');
    return this._notificationRegistry.get(channelId);
  }

  public listNotificationChannels(): ReadonlyArray<INotificationChannel> {
    this.ensureReady('listNotificationChannels');
    return this._notificationRegistry.list();
  }

  public enableNotificationChannel(channelId: string): void {
    this.ensureReady('enableNotificationChannel');
    this._notificationRegistry.enable(channelId);
  }

  public disableNotificationChannel(channelId: string): void {
    this.ensureReady('disableNotificationChannel');
    this._notificationRegistry.disable(channelId);
  }

  public dispatchNotification(request: NotificationRequest, maxAttempts?: number): Promise<NotificationDeliveryResult> {
    this.ensureReady('dispatchNotification');
    return this._notificationDispatcher.dispatch(request, maxAttempts);
  }

  public getNotificationDeliveryHistory(): ReadonlyArray<NotificationDeliveryResult> {
    this.ensureReady('getNotificationDeliveryHistory');
    return this._notificationDispatcher.getHistory();
  }

  // --- Orchestration APIs ---
  public orchestrate(request: AlertOrchestrationRequest): Promise<AlertOrchestrationResult> {
    this.ensureReady('orchestrate');
    return this._orchestrator.orchestrate(request);
  }

  public orchestrateMany(requests: ReadonlyArray<AlertOrchestrationRequest>): Promise<ReadonlyArray<AlertOrchestrationResult>> {
    this.ensureReady('orchestrateMany');
    return this._orchestrator.orchestrateMany(requests);
  }

  public getResult(orchestrationId: string): AlertOrchestrationResult | null {
    this.ensureReady('getResult');
    return this._orchestrator.getResult(orchestrationId);
  }

  public getHistory(): ReadonlyArray<AlertOrchestrationResult> {
    this.ensureReady('getHistory');
    return this._orchestrator.getHistory();
  }

  // --- Certification APIs ---
  public certify(): Promise<AlertCertificationReport> {
    this.ensureReady('certify');
    return this._certifier.certify();
  }

  public certifyStage(stage: AlertCertificationStageValue): Promise<AlertCertificationStageResult> {
    this.ensureReady('certifyStage');
    return this._certifier.certifyStage(stage);
  }

  public getReport(): AlertCertificationReport | null {
    this.ensureReady('getReport');
    return this._certifier.getReport();
  }

  public reset(): void {
    this.ensureReady('reset');
    this._certifier.reset();
  }

  private clearEvaluationStats(): void {
    this._totalEvaluations = 0;
    this._matchedEvaluations = 0;
    this._unmatchedEvaluations = 0;
    this._errorEvaluations = 0;
    this._skippedEvaluations = 0;
    this._totalEvaluationDuration = 0;
  }

  private clearGenerationStats(): void {
    this._totalAlertGenerations = 0;
    this._successfulAlertGenerations = 0;
    this._rejectedAlertGenerations = 0;
    this._generationErrors = 0;
    this._totalGenerationDuration = 0;
  }

  private clearDeduplicationStats(): void {
    this._totalDeduplicationChecks = 0;
    this._acceptedAlertCount = 0;
    this._duplicateAlertCount = 0;
    this._cooldownSuppressedCount = 0;
  }

  // --- Statistics & Diagnostics ---
  public getStatistics(): AlertingStatistics {
    this.ensureReady('getStatistics');
    const alertCount = this._registry.listAlerts().length;
    const rules = this._registry.listRules();
    const ruleCount = rules.length;
    const enabledRuleCount = rules.filter(r => r.enabled).length;
    const disabledRuleCount = ruleCount - enabledRuleCount;
    const averageEvaluationDuration = this._totalEvaluations > 0 ? this._totalEvaluationDuration / this._totalEvaluations : 0;
    const averageGenerationDuration = this._totalAlertGenerations > 0 ? this._totalGenerationDuration / this._totalAlertGenerations : 0;

    const dedupDiags = this._deduplicator.getDiagnostics(Date.now());
    const lifecycleStats = this._lifecycleManager.getTransitionStats();
    const suppressionStats = this._suppressionManager.getStats();

    const channels = this._notificationRegistry.list();
    const registeredChannels = channels.length;
    const enabledChannels = channels.filter(c => c.enabled).length;
    const disabledChannels = registeredChannels - enabledChannels;
    const notificationStats = this._notificationDispatcher.getStats();
    const orchestrationStats = this._orchestrator.getStats();

    return createAlertingStatistics({
      registeredAlertCount: alertCount,
      registeredRuleCount: ruleCount,
      enabledRuleCount,
      disabledRuleCount,
      totalEvaluations: this._totalEvaluations,
      matchedEvaluations: this._matchedEvaluations,
      unmatchedEvaluations: this._unmatchedEvaluations,
      errorEvaluations: this._errorEvaluations,
      skippedEvaluations: this._skippedEvaluations,
      totalEvaluationDuration: this._totalEvaluationDuration,
      averageEvaluationDuration,
      totalAlertGenerations: this._totalAlertGenerations,
      successfulAlertGenerations: this._successfulAlertGenerations,
      rejectedAlertGenerations: this._rejectedAlertGenerations,
      generationErrors: this._generationErrors,
      totalGenerationDuration: this._totalGenerationDuration,
      averageGenerationDuration,
      totalDeduplicationChecks: this._totalDeduplicationChecks,
      acceptedAlertCount: this._acceptedAlertCount,
      duplicateAlertCount: this._duplicateAlertCount,
      cooldownSuppressedCount: this._cooldownSuppressedCount,
      activeCooldownCount: dedupDiags.activeCooldownCount,
      trackedFingerprintCount: dedupDiags.trackedFingerprintCount,
      lifecycleTransitions: lifecycleStats.lifecycleTransitions,
      acknowledgements: lifecycleStats.acknowledgements,
      resolutions: lifecycleStats.resolutions,
      closures: lifecycleStats.closures,
      invalidTransitions: lifecycleStats.invalidTransitions,
      activeAlerts: lifecycleStats.activeAlerts,
      acknowledgedAlerts: lifecycleStats.acknowledgedAlerts,
      resolvedAlerts: lifecycleStats.resolvedAlerts,
      closedAlerts: lifecycleStats.closedAlerts,
      suppressionEvaluations: suppressionStats.suppressionEvaluations,
      suppressedAlerts: suppressionStats.suppressedAlerts,
      allowedAlerts: suppressionStats.allowedAlerts,
      policyMatches: suppressionStats.policyMatches,
      maintenanceMatches: suppressionStats.maintenanceMatches,
      snoozedMatches: suppressionStats.snoozedMatches,
      evaluationFailures: suppressionStats.evaluationFailures,
      activePolicies: suppressionStats.activePolicies,
      activeMaintenanceWindows: suppressionStats.activeMaintenanceWindows,
      activeSnoozes: suppressionStats.activeSnoozes,
      notificationRequests: notificationStats.notificationRequests,
      validationFailures: notificationStats.validationFailures,
      dispatchedNotifications: notificationStats.dispatchedNotifications,
      deliveredNotifications: notificationStats.deliveredNotifications,
      failedNotifications: notificationStats.failedNotifications,
      skippedNotifications: notificationStats.skippedNotifications,
      cancelledNotifications: notificationStats.cancelledNotifications,
      retryAttempts: notificationStats.retryAttempts,
      registeredChannels,
      enabledChannels,
      disabledChannels,
      averageDeliveryDuration: notificationStats.averageDeliveryDuration,
      orchestrationsTotal: orchestrationStats.orchestrationsTotal,
      orchestrationsSuccessful: orchestrationStats.orchestrationsSuccessful,
      orchestrationsSkipped: orchestrationStats.orchestrationsSkipped,
      orchestrationsDuplicate: orchestrationStats.orchestrationsDuplicate,
      orchestrationsSuppressed: orchestrationStats.orchestrationsSuppressed,
      orchestrationsFailed: orchestrationStats.orchestrationsFailed,
      averageOrchestrationDuration: orchestrationStats.averageOrchestrationDuration,
      activeOrchestrations: orchestrationStats.activeOrchestrations
    });
  }

  public getDiagnostics(): AlertingDiagnostics {
    this.ensureReady('getDiagnostics');
    const alertCount = this._registry.listAlerts().length;
    const rules = this._registry.listRules();
    const ruleCount = rules.length;
    const enabledRuleCount = rules.filter(r => r.enabled).length;
    const disabledRuleCount = ruleCount - enabledRuleCount;
    const averageEvaluationDuration = this._totalEvaluations > 0 ? this._totalEvaluationDuration / this._totalEvaluations : 0;
    const averageGenerationDuration = this._totalAlertGenerations > 0 ? this._totalGenerationDuration / this._totalAlertGenerations : 0;

    const now = Date.now();
    const dedupDiags = this._deduplicator.getDiagnostics(now);
    const lifecycleStats = this._lifecycleManager.getTransitionStats();
    const suppressionStats = this._suppressionManager.getStats();

    const channels = this._notificationRegistry.list();
    const registeredChannels = channels.length;
    const enabledChannels = channels.filter(c => c.enabled).length;
    const disabledChannels = registeredChannels - enabledChannels;
    const notificationStats = this._notificationDispatcher.getStats();
    const orchestrationStats = this._orchestrator.getStats();

    return createAlertingDiagnostics({
      runtimeState: this._state,
      registeredAlertCount: alertCount,
      registeredRuleCount: ruleCount,
      enabledRuleCount,
      disabledRuleCount,
      totalEvaluations: this._totalEvaluations,
      matchedEvaluations: this._matchedEvaluations,
      unmatchedEvaluations: this._unmatchedEvaluations,
      errorEvaluations: this._errorEvaluations,
      skippedEvaluations: this._skippedEvaluations,
      totalEvaluationDuration: this._totalEvaluationDuration,
      averageEvaluationDuration,
      totalAlertGenerations: this._totalAlertGenerations,
      successfulAlertGenerations: this._successfulAlertGenerations,
      rejectedAlertGenerations: this._rejectedAlertGenerations,
      generationErrors: this._generationErrors,
      totalGenerationDuration: this._totalGenerationDuration,
      averageGenerationDuration,
      totalDeduplicationChecks: this._totalDeduplicationChecks,
      acceptedAlertCount: this._acceptedAlertCount,
      duplicateAlertCount: this._duplicateAlertCount,
      cooldownSuppressedCount: this._cooldownSuppressedCount,
      activeCooldownCount: dedupDiags.activeCooldownCount,
      trackedFingerprintCount: dedupDiags.trackedFingerprintCount,
      lifecycleTransitions: lifecycleStats.lifecycleTransitions,
      acknowledgements: lifecycleStats.acknowledgements,
      resolutions: lifecycleStats.resolutions,
      closures: lifecycleStats.closures,
      invalidTransitions: lifecycleStats.invalidTransitions,
      activeAlerts: lifecycleStats.activeAlerts,
      acknowledgedAlerts: lifecycleStats.acknowledgedAlerts,
      resolvedAlerts: lifecycleStats.resolvedAlerts,
      closedAlerts: lifecycleStats.closedAlerts,
      suppressionEvaluations: suppressionStats.suppressionEvaluations,
      suppressedAlerts: suppressionStats.suppressedAlerts,
      allowedAlerts: suppressionStats.allowedAlerts,
      policyMatches: suppressionStats.policyMatches,
      maintenanceMatches: suppressionStats.maintenanceMatches,
      snoozedMatches: suppressionStats.snoozedMatches,
      evaluationFailures: suppressionStats.evaluationFailures,
      activePolicies: suppressionStats.activePolicies,
      activeMaintenanceWindows: suppressionStats.activeMaintenanceWindows,
      activeSnoozes: suppressionStats.activeSnoozes,
      notificationRequests: notificationStats.notificationRequests,
      validationFailures: notificationStats.validationFailures,
      dispatchedNotifications: notificationStats.dispatchedNotifications,
      deliveredNotifications: notificationStats.deliveredNotifications,
      failedNotifications: notificationStats.failedNotifications,
      skippedNotifications: notificationStats.skippedNotifications,
      cancelledNotifications: notificationStats.cancelledNotifications,
      retryAttempts: notificationStats.retryAttempts,
      registeredChannels,
      enabledChannels,
      disabledChannels,
      averageDeliveryDuration: notificationStats.averageDeliveryDuration,
      orchestrationsTotal: orchestrationStats.orchestrationsTotal,
      orchestrationsSuccessful: orchestrationStats.orchestrationsSuccessful,
      orchestrationsSkipped: orchestrationStats.orchestrationsSkipped,
      orchestrationsDuplicate: orchestrationStats.orchestrationsDuplicate,
      orchestrationsSuppressed: orchestrationStats.orchestrationsSuppressed,
      orchestrationsFailed: orchestrationStats.orchestrationsFailed,
      averageOrchestrationDuration: orchestrationStats.averageOrchestrationDuration,
      activeOrchestrations: orchestrationStats.activeOrchestrations,
      generatedAt: now
    });
  }
}
