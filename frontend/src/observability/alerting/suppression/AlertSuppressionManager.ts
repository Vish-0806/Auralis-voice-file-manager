import { AlertRecord } from '../models/alert';
import {
  AlertSuppressionPolicy,
  AlertMaintenanceWindow,
  AlertSnoozeRecord,
  AlertSuppressionDecision
} from '../models/suppression';
import {
  AlertSuppressionError,
  AlertSuppressionPolicyError,
  AlertMaintenanceWindowError,
  AlertSnoozeError,
  AlertSuppressionEvaluationError
} from '../errors/AlertingErrors';
import {
  createAlertSuppressionPolicy,
  createAlertMaintenanceWindow,
  createAlertSnoozeRecord,
  createAlertSuppressionDecision
} from '../factories/alertingFactories';

export class AlertSuppressionManager {
  private readonly _policies = new Map<string, AlertSuppressionPolicy>();
  private readonly _maintenanceWindows = new Map<string, AlertMaintenanceWindow>();
  private readonly _snoozes = new Map<string, AlertSnoozeRecord>();
  private readonly _history: AlertSuppressionDecision[] = [];
  private readonly _maxHistorySize: number;

  private _suppressionEvaluations = 0;
  private _suppressedAlerts = 0;
  private _allowedAlerts = 0;
  private _policyMatches = 0;
  private _maintenanceMatches = 0;
  private _snoozedMatches = 0;
  private _evaluationFailures = 0;

  constructor(maxHistorySize = 1000) {
    this._maxHistorySize = maxHistorySize;
  }

  // --- Policy Management ---
  public registerPolicy(policy: AlertSuppressionPolicy): void {
    if (!policy) {
      throw new AlertSuppressionPolicyError('Policy is required');
    }
    if (this._policies.has(policy.id)) {
      throw new AlertSuppressionPolicyError(`Policy with ID ${policy.id} already exists`);
    }

    try {
      const validatedPolicy = createAlertSuppressionPolicy(policy);
      this._policies.set(validatedPolicy.id, validatedPolicy);
    } catch (err: any) {
      throw new AlertSuppressionPolicyError(err.message || 'Failed to register policy');
    }
  }

  public unregisterPolicy(policyId: string): void {
    if (!policyId) {
      throw new AlertSuppressionPolicyError('Policy ID is required');
    }
    if (!this._policies.has(policyId)) {
      throw new AlertSuppressionPolicyError(`Policy with ID ${policyId} not found`);
    }
    this._policies.delete(policyId);
  }

  public listPolicies(): ReadonlyArray<AlertSuppressionPolicy> {
    return Array.from(this._policies.values());
  }

  // --- Maintenance Windows ---
  public registerMaintenanceWindow(window: AlertMaintenanceWindow): void {
    if (!window) {
      throw new AlertMaintenanceWindowError('Maintenance window is required');
    }
    if (this._maintenanceWindows.has(window.id)) {
      throw new AlertMaintenanceWindowError(`Maintenance window with ID ${window.id} already exists`);
    }

    try {
      const validatedWindow = createAlertMaintenanceWindow(window);
      this._maintenanceWindows.set(validatedWindow.id, validatedWindow);
    } catch (err: any) {
      throw new AlertMaintenanceWindowError(err.message || 'Failed to register maintenance window');
    }
  }

  public unregisterMaintenanceWindow(windowId: string): void {
    if (!windowId) {
      throw new AlertMaintenanceWindowError('Maintenance window ID is required');
    }
    if (!this._maintenanceWindows.has(windowId)) {
      throw new AlertMaintenanceWindowError(`Maintenance window with ID ${windowId} not found`);
    }
    this._maintenanceWindows.delete(windowId);
  }

  public listMaintenanceWindows(): ReadonlyArray<AlertMaintenanceWindow> {
    return Array.from(this._maintenanceWindows.values());
  }

  // --- Snoozing ---
  public snoozeAlert(
    alertId: string,
    fingerprint: string | undefined,
    durationMs: number,
    actor: string,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertSnoozeRecord {
    if (!alertId) {
      throw new AlertSnoozeError('Alert ID is required for snoozing');
    }
    if (typeof durationMs !== 'number' || isNaN(durationMs) || durationMs <= 0) {
      throw new AlertSnoozeError('Snooze duration must be a valid positive number');
    }

    const start = now !== undefined ? now : Date.now();
    const end = start + durationMs;

    try {
      const snooze = createAlertSnoozeRecord({
        alertId,
        fingerprint,
        startTime: start,
        endTime: end,
        actor,
        reason,
        metadata
      });

      this._snoozes.set(alertId, snooze);
      return snooze;
    } catch (err: any) {
      throw new AlertSnoozeError(err.message || 'Failed to create snooze');
    }
  }

  public clearSnooze(alertId: string): void {
    if (!alertId) {
      throw new AlertSnoozeError('Alert ID is required');
    }
    this._snoozes.delete(alertId);
  }

  public getSnooze(alertId: string): AlertSnoozeRecord | null {
    return this._snoozes.get(alertId) || null;
  }

  public isSnoozed(alertId: string, now: number): boolean {
    const snooze = this._snoozes.get(alertId);
    if (!snooze) return false;
    return now >= snooze.startTime && now < snooze.endTime;
  }

  // --- Evaluation ---
  public evaluateSuppression(alert: AlertRecord, now?: number): AlertSuppressionDecision {
    if (!alert) {
      throw new AlertSuppressionEvaluationError('alert is required for suppression evaluation');
    }
    const timestamp = now !== undefined ? now : Date.now();

    if (typeof timestamp !== 'number' || isNaN(timestamp) || !isFinite(timestamp) || timestamp < 0) {
      this._evaluationFailures++;
      throw new AlertSuppressionEvaluationError(`Invalid timestamp for evaluation: ${timestamp}`);
    }

    this._suppressionEvaluations++;

    try {
      // 1. Explicit alert snooze
      const snooze = this._snoozes.get(alert.id);
      if (snooze && timestamp >= snooze.startTime && timestamp < snooze.endTime) {
        this._snoozedMatches++;
        this._suppressedAlerts++;
        const decision = createAlertSuppressionDecision({
          suppressed: true,
          reason: 'SNOOZED',
          evaluatedAt: timestamp,
          metadata: snooze.metadata
        });
        this.logDecision(decision);
        return decision;
      }

      // Collect all active enabled policies
      const activePolicies = Array.from(this._policies.values()).filter(p => {
        if (!p.enabled) return false;
        if (p.startTime !== undefined && timestamp < p.startTime) return false;
        if (p.endTime !== undefined && timestamp >= p.endTime) return false;
        return true;
      });

      // Scope precedence helper: ALERT, FINGERPRINT, RULE, SOURCE
      const scopes = ['ALERT', 'FINGERPRINT', 'RULE', 'SOURCE'] as const;
      for (const scope of scopes) {
        const matching = activePolicies.filter(p => {
          if (p.scope !== scope) return false;
          if (scope === 'ALERT' && p.alertId !== alert.id) return false;
          if (scope === 'FINGERPRINT' && p.fingerprint !== alert.fingerprint) return false;
          if (scope === 'RULE' && p.ruleId !== alert.ruleId) return false;
          if (scope === 'SOURCE' && p.sourceId !== alert.sourceId) return false;
          return true;
        });

        if (matching.length > 0) {
          matching.sort((a, b) => {
            if (a.priority !== b.priority) {
              return b.priority - a.priority;
            }
            return a.id.localeCompare(b.id);
          });

          const winner = matching[0];
          this._policyMatches++;
          this._suppressedAlerts++;
          const decision = createAlertSuppressionDecision({
            suppressed: true,
            reason: winner.reason,
            policyId: winner.id,
            evaluatedAt: timestamp,
            metadata: winner.metadata
          });
          this.logDecision(decision);
          return decision;
        }
      }

      // 6. Maintenance window
      const activeMaintenance = Array.from(this._maintenanceWindows.values()).find(mw => {
        if (!mw.enabled) return false;
        if (timestamp < mw.startTime || timestamp >= mw.endTime) return false;
        if (mw.scope) {
          if (mw.scope === 'ALERT' && mw.metadata?.alertId !== alert.id) return false;
          if (mw.scope === 'FINGERPRINT' && mw.metadata?.fingerprint !== alert.fingerprint) return false;
          if (mw.scope === 'RULE' && mw.metadata?.ruleId !== alert.ruleId) return false;
          if (mw.scope === 'SOURCE' && mw.metadata?.sourceId !== alert.sourceId) return false;
        }
        return true;
      });

      if (activeMaintenance) {
        this._maintenanceMatches++;
        this._suppressedAlerts++;
        const decision = createAlertSuppressionDecision({
          suppressed: true,
          reason: 'MAINTENANCE',
          windowId: activeMaintenance.id,
          evaluatedAt: timestamp,
          metadata: activeMaintenance.metadata
        });
        this.logDecision(decision);
        return decision;
      }

      // 7. Global policy
      const globalPolicies = activePolicies.filter(p => p.scope === 'GLOBAL');
      if (globalPolicies.length > 0) {
        globalPolicies.sort((a, b) => {
          if (a.priority !== b.priority) {
            return b.priority - a.priority;
          }
          return a.id.localeCompare(b.id);
        });

        const winner = globalPolicies[0];
        this._policyMatches++;
        this._suppressedAlerts++;
        const decision = createAlertSuppressionDecision({
          suppressed: true,
          reason: winner.reason,
          policyId: winner.id,
          evaluatedAt: timestamp,
          metadata: winner.metadata
        });
        this.logDecision(decision);
        return decision;
      }

      this._allowedAlerts++;
      const decision = createAlertSuppressionDecision({
        suppressed: false,
        reason: null,
        evaluatedAt: timestamp
      });
      this.logDecision(decision);
      return decision;
    } catch (err: any) {
      this._evaluationFailures++;
      if (err instanceof AlertSuppressionError) {
        throw err;
      }
      throw new AlertSuppressionEvaluationError(err.message || 'Internal evaluation failure');
    }
  }

  // --- Reset/All-clear ---
  public clearAll(): void {
    this._policies.clear();
    this._maintenanceWindows.clear();
    this._snoozes.clear();
    this._history.length = 0;
    this._suppressionEvaluations = 0;
    this._suppressedAlerts = 0;
    this._allowedAlerts = 0;
    this._policyMatches = 0;
    this._maintenanceMatches = 0;
    this._snoozedMatches = 0;
    this._evaluationFailures = 0;
  }

  // --- Stats and Diagnostics getters ---
  public getStats() {
    return {
      suppressionEvaluations: this._suppressionEvaluations,
      suppressedAlerts: this._suppressedAlerts,
      allowedAlerts: this._allowedAlerts,
      policyMatches: this._policyMatches,
      maintenanceMatches: this._maintenanceMatches,
      snoozedMatches: this._snoozedMatches,
      evaluationFailures: this._evaluationFailures,
      activePolicies: this._policies.size,
      activeMaintenanceWindows: this._maintenanceWindows.size,
      activeSnoozes: this._snoozes.size
    };
  }

  public getDiagnostics(now: number) {
    let enabledPoliciesCount = 0;
    for (const p of this._policies.values()) {
      if (p.enabled) enabledPoliciesCount++;
    }

    let activeWindowsCount = 0;
    for (const mw of this._maintenanceWindows.values()) {
      if (mw.enabled && now >= mw.startTime && now < mw.endTime) {
        activeWindowsCount++;
      }
    }

    let activeSnoozesCount = 0;
    for (const sz of this._snoozes.values()) {
      if (now >= sz.startTime && now < sz.endTime) {
        activeSnoozesCount++;
      }
    }

    return {
      registeredPoliciesCount: this._policies.size,
      enabledPoliciesCount,
      activeMaintenanceWindowsCount: activeWindowsCount,
      activeSnoozesCount,
      historySize: this._history.length
    };
  }

  private logDecision(decision: AlertSuppressionDecision): void {
    this._history.push(decision);
    if (this._history.length > this._maxHistorySize) {
      this._history.shift();
    }
  }
}
