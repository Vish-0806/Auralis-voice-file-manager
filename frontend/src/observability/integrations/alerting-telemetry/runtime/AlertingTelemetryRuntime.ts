import { IAlertingTelemetryRuntime } from '../interfaces/alerting-telemetry-runtime';
import { IAlertingTelemetryProvider } from '../interfaces/alerting-telemetry-provider';
import { AlertingTelemetryProvider } from '../provider/AlertingTelemetryProvider';
import { ITelemetryRuntime } from '../../../telemetry/interfaces/telemetry-runtime';
import {
  AlertingTelemetryPolicy,
  AlertingTelemetryTrigger,
  AlertingTelemetryResult,
  AlertingTelemetryStatistics,
  AlertingTelemetryDiagnostics
} from '../models';

export class AlertingTelemetryRuntime implements IAlertingTelemetryRuntime {
  private readonly _provider: IAlertingTelemetryProvider;

  constructor(
    providerOrDependencies:
      | IAlertingTelemetryProvider
      | { telemetryRuntime: ITelemetryRuntime }
  ) {
    if (
      providerOrDependencies &&
      typeof (providerOrDependencies as any).integrate === 'function'
    ) {
      this._provider = providerOrDependencies as IAlertingTelemetryProvider;
    } else {
      this._provider = new AlertingTelemetryProvider(
        providerOrDependencies as { telemetryRuntime: ITelemetryRuntime }
      );
    }
  }

  public provider(): IAlertingTelemetryProvider {
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

  public registerPolicy(policy: AlertingTelemetryPolicy): void {
    this._provider.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this._provider.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): AlertingTelemetryPolicy | null {
    return this._provider.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<AlertingTelemetryPolicy> {
    return this._provider.listPolicies();
  }

  public enablePolicy(policyId: string): void {
    this._provider.enablePolicy(policyId);
  }

  public disablePolicy(policyId: string): void {
    this._provider.disablePolicy(policyId);
  }

  public integrate(trigger: AlertingTelemetryTrigger): Promise<AlertingTelemetryResult> {
    return this._provider.integrate(trigger);
  }

  public integrateBatch(triggers: ReadonlyArray<AlertingTelemetryTrigger>): Promise<ReadonlyArray<AlertingTelemetryResult>> {
    return this._provider.integrateBatch(triggers);
  }

  public statistics(): AlertingTelemetryStatistics {
    return this._provider.statistics();
  }

  public diagnostics(): AlertingTelemetryDiagnostics {
    return this._provider.diagnostics();
  }
}
