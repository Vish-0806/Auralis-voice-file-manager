import { IDiagnosticsTelemetryRuntime } from '../interfaces/diagnostics-telemetry-runtime';
import { IDiagnosticsTelemetryProvider } from '../interfaces/diagnostics-telemetry-provider';
import { DiagnosticsTelemetryProvider } from '../provider/DiagnosticsTelemetryProvider';
import { ITelemetryRuntime } from '../../../telemetry/interfaces/telemetry-runtime';
import {
  DiagnosticsTelemetryPolicy,
  DiagnosticsTelemetryResult,
  DiagnosticsTelemetryStatistics,
  DiagnosticsTelemetryDiagnostics
} from '../models';
import { DiagnosticReport } from '../../../diagnostics/models/report';

export class DiagnosticsTelemetryRuntime implements IDiagnosticsTelemetryRuntime {
  private readonly _provider: IDiagnosticsTelemetryProvider;

  constructor(
    providerOrDependencies:
      | IDiagnosticsTelemetryProvider
      | { telemetryRuntime: ITelemetryRuntime }
  ) {
    if (
      providerOrDependencies &&
      typeof (providerOrDependencies as any).processDiagnosticReport === 'function'
    ) {
      this._provider = providerOrDependencies as IDiagnosticsTelemetryProvider;
    } else {
      this._provider = new DiagnosticsTelemetryProvider(
        providerOrDependencies as { telemetryRuntime: ITelemetryRuntime }
      );
    }
  }

  public provider(): IDiagnosticsTelemetryProvider {
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

  public getStatistics(): DiagnosticsTelemetryStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): DiagnosticsTelemetryDiagnostics {
    return this._provider.getDiagnostics();
  }

  public registerPolicy(policy: DiagnosticsTelemetryPolicy): void {
    this._provider.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this._provider.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): DiagnosticsTelemetryPolicy | null {
    return this._provider.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<DiagnosticsTelemetryPolicy> {
    return this._provider.listPolicies();
  }

  public enablePolicy(policyId: string): void {
    this._provider.enablePolicy(policyId);
  }

  public disablePolicy(policyId: string): void {
    this._provider.disablePolicy(policyId);
  }

  public processDiagnosticReport(report: DiagnosticReport): Promise<ReadonlyArray<DiagnosticsTelemetryResult>> {
    return this._provider.processDiagnosticReport(report);
  }
}
