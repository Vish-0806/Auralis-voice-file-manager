import type { IAlertingProvider } from '../interfaces/alerting-provider';
import type { AlertRecord } from '../models/alert';
import type { AlertRule } from '../models/alert-rule';
import { AlertingRuntimeState, AlertingRuntimeStateValue } from '../models/runtime';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import { AlertRegistry } from '../registry/AlertRegistry';
import { AlertingStateError } from '../errors/AlertingErrors';
import { createAlertingStatistics, createAlertingDiagnostics } from '../factories/alertingFactories';

export class AlertingProvider implements IAlertingProvider {
  private _state: AlertingRuntimeStateValue = AlertingRuntimeState.UNINITIALIZED;
  private readonly _registry = new AlertRegistry();

  private ensureReady(action: string): void {
    if (this._state !== AlertingRuntimeState.READY) {
      throw new AlertingStateError(`Cannot perform action '${action}' when state is ${this._state}. Provider must be READY.`);
    }
  }

  public async initialize(): Promise<void> {
    if (this._state === AlertingRuntimeState.READY) {
      return; // idempotent
    }
    if (this._state === AlertingRuntimeState.INITIALIZING || this._state === AlertingRuntimeState.STOPPING || this._state === AlertingRuntimeState.STOPPED) {
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
      return; // idempotent
    }
    if (this._state === AlertingRuntimeState.UNINITIALIZED) {
      throw new AlertingStateError('Cannot shutdown alerting provider: it is not initialized.');
    }

    this._state = AlertingRuntimeState.STOPPING;
    try {
      this._registry.clear();
      this._registry.clearRules();
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
    return this._registry.removeAlert(alertId);
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    this.ensureReady('listAlerts');
    return this._registry.listAlerts();
  }

  public clearAlerts(): void {
    this.ensureReady('clearAlerts');
    this._registry.clear();
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

  // --- Statistics & Diagnostics ---
  public getStatistics(): AlertingStatistics {
    this.ensureReady('getStatistics');
    const alertCount = this._registry.listAlerts().length;
    const rules = this._registry.listRules();
    const ruleCount = rules.length;
    const enabledRuleCount = rules.filter(r => r.enabled).length;
    const disabledRuleCount = ruleCount - enabledRuleCount;

    return createAlertingStatistics({
      registeredAlertCount: alertCount,
      registeredRuleCount: ruleCount,
      enabledRuleCount,
      disabledRuleCount
    });
  }

  public getDiagnostics(): AlertingDiagnostics {
    this.ensureReady('getDiagnostics');
    const alertCount = this._registry.listAlerts().length;
    const rules = this._registry.listRules();
    const ruleCount = rules.length;
    const enabledRuleCount = rules.filter(r => r.enabled).length;
    const disabledRuleCount = ruleCount - enabledRuleCount;

    return createAlertingDiagnostics({
      runtimeState: this._state,
      registeredAlertCount: alertCount,
      registeredRuleCount: ruleCount,
      enabledRuleCount,
      disabledRuleCount,
      generatedAt: Date.now()
    });
  }
}
