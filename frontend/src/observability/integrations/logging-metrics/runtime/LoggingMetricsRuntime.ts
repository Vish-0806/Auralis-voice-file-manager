import { ILoggingMetricsRuntime } from '../interfaces/logging-metrics-runtime';
import { ILoggingMetricsProvider } from '../interfaces/logging-metrics-provider';
import { LoggingMetricsProvider } from '../provider/LoggingMetricsProvider';
import { IMetricsRuntime } from '../../../metrics/interfaces/metrics-runtime';
import {
  LoggingMetricsPolicy,
  LoggingMetricResult,
  LoggingMetricsStatistics,
  LoggingMetricsDiagnostics
} from '../models';
import { LogRecord } from '../../../logging/models/log';

export class LoggingMetricsRuntime implements ILoggingMetricsRuntime {
  private readonly _provider: ILoggingMetricsProvider;

  constructor(
    providerOrDependencies:
      | ILoggingMetricsProvider
      | { metricsRuntime: IMetricsRuntime }
  ) {
    if (
      providerOrDependencies &&
      typeof (providerOrDependencies as any).processLogRecord === 'function'
    ) {
      this._provider = providerOrDependencies as ILoggingMetricsProvider;
    } else {
      this._provider = new LoggingMetricsProvider(
        providerOrDependencies as { metricsRuntime: IMetricsRuntime }
      );
    }
  }

  public provider(): ILoggingMetricsProvider {
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

  public getStatistics(): LoggingMetricsStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): LoggingMetricsDiagnostics {
    return this._provider.getDiagnostics();
  }

  public registerPolicy(policy: LoggingMetricsPolicy): void {
    this._provider.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this._provider.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): LoggingMetricsPolicy | null {
    return this._provider.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<LoggingMetricsPolicy> {
    return this._provider.listPolicies();
  }

  public enablePolicy(policyId: string): void {
    this._provider.enablePolicy(policyId);
  }

  public disablePolicy(policyId: string): void {
    this._provider.disablePolicy(policyId);
  }

  public processLogRecord(record: LogRecord): Promise<LoggingMetricResult> {
    return this._provider.processLogRecord(record);
  }
}
