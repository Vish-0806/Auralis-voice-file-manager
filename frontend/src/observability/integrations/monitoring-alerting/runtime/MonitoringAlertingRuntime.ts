import { IMonitoringAlertingRuntime } from '../interfaces/monitoring-alerting-runtime';
import { IMonitoringAlertingProvider } from '../interfaces/monitoring-alerting-provider';
import { MonitoringAlertingProvider } from '../provider/MonitoringAlertingProvider';
import { IAlertingRuntime } from '../../../alerting/interfaces/alerting-runtime';
import { ICorrelationRuntime } from '../../../correlation/interfaces/correlation-runtime';
import {
  MonitoringAlertPolicy,
  MonitoringAlertIntegrationResult,
  MonitoringAlertIntegrationStatistics,
  MonitoringAlertIntegrationDiagnostics
} from '../models';
import { MonitoringResult } from '../../../models/monitoring';

export class MonitoringAlertingRuntime implements IMonitoringAlertingRuntime {
  private readonly _provider: IMonitoringAlertingProvider;

  constructor(
    providerOrDependencies:
      | IMonitoringAlertingProvider
      | { alertingRuntime: IAlertingRuntime; correlationRuntime: ICorrelationRuntime }
  ) {
    if (
      providerOrDependencies &&
      typeof (providerOrDependencies as any).processResult === 'function'
    ) {
      this._provider = providerOrDependencies as IMonitoringAlertingProvider;
    } else {
      this._provider = new MonitoringAlertingProvider(
        providerOrDependencies as { alertingRuntime: IAlertingRuntime; correlationRuntime: ICorrelationRuntime }
      );
    }
  }

  public provider(): IMonitoringAlertingProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): string {
    return this._provider.getState();
  }

  public getHealth(): string {
    return this._provider.getHealth();
  }

  public getStatistics(): MonitoringAlertIntegrationStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): MonitoringAlertIntegrationDiagnostics {
    return this._provider.getDiagnostics();
  }

  public registerPolicy(policy: MonitoringAlertPolicy): void {
    this._provider.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this._provider.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): MonitoringAlertPolicy | null {
    return this._provider.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<MonitoringAlertPolicy> {
    return this._provider.listPolicies();
  }

  public enablePolicy(policyId: string): void {
    this._provider.enablePolicy(policyId);
  }

  public disablePolicy(policyId: string): void {
    this._provider.disablePolicy(policyId);
  }

  public processResult(result: MonitoringResult): Promise<MonitoringAlertIntegrationResult> {
    return this._provider.processResult(result);
  }
}
