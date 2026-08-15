import type { IAlertingProvider } from '../interfaces/alerting-provider';
import type { AlertRecord } from '../models/alert';
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
    this._registry.removeAlert(alertId);
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    this.ensureReady('listAlerts');
    return this._registry.listAlerts();
  }

  public clearAlerts(): void {
    this.ensureReady('clearAlerts');
    this._registry.clear();
  }

  public getStatistics(): AlertingStatistics {
    this.ensureReady('getStatistics');
    const count = this._registry.listAlerts().length;
    return createAlertingStatistics({ registeredAlertCount: count });
  }

  public getDiagnostics(): AlertingDiagnostics {
    this.ensureReady('getDiagnostics');
    const count = this._registry.listAlerts().length;
    return createAlertingDiagnostics({
      runtimeState: this._state,
      registeredAlertCount: count,
      generatedAt: Date.now()
    });
  }
}
