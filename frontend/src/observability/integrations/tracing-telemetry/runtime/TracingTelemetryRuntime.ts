import { ITracingTelemetryRuntime } from '../interfaces/tracing-telemetry-runtime';
import { ITracingTelemetryProvider } from '../interfaces/tracing-telemetry-provider';
import { TracingTelemetryProvider } from '../provider/TracingTelemetryProvider';
import { ITelemetryRuntime } from '../../../telemetry/interfaces/telemetry-runtime';
import {
  TracingTelemetryPolicy,
  TracingTelemetryResult,
  TracingTelemetryStatistics,
  TracingTelemetryDiagnostics
} from '../models';
import { Span } from '../../../tracing/models/span';

export class TracingTelemetryRuntime implements ITracingTelemetryRuntime {
  private readonly _provider: ITracingTelemetryProvider;

  constructor(
    providerOrDependencies:
      | ITracingTelemetryProvider
      | { telemetryRuntime: ITelemetryRuntime }
  ) {
    if (
      providerOrDependencies &&
      typeof (providerOrDependencies as any).processCompletedSpan === 'function'
    ) {
      this._provider = providerOrDependencies as ITracingTelemetryProvider;
    } else {
      this._provider = new TracingTelemetryProvider(
        providerOrDependencies as { telemetryRuntime: ITelemetryRuntime }
      );
    }
  }

  public provider(): ITracingTelemetryProvider {
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

  public getStatistics(): TracingTelemetryStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): TracingTelemetryDiagnostics {
    return this._provider.getDiagnostics();
  }

  public registerPolicy(policy: TracingTelemetryPolicy): void {
    this._provider.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this._provider.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): TracingTelemetryPolicy | null {
    return this._provider.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<TracingTelemetryPolicy> {
    return this._provider.listPolicies();
  }

  public enablePolicy(policyId: string): void {
    this._provider.enablePolicy(policyId);
  }

  public disablePolicy(policyId: string): void {
    this._provider.disablePolicy(policyId);
  }

  public processCompletedSpan(span: Span): Promise<TracingTelemetryResult> {
    return this._provider.processCompletedSpan(span);
  }
}
