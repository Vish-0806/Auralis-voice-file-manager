import type { IAlertingRuntime } from '../interfaces/alerting-runtime';
import type { IAlertingProvider } from '../interfaces/alerting-provider';
import { AlertingProvider } from '../provider/AlertingProvider';
import type { AlertRecord } from '../models/alert';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import type { AlertingRuntimeStateValue } from '../models/runtime';

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

  public getStatistics(): AlertingStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): AlertingDiagnostics {
    return this._provider.getDiagnostics();
  }
}
