import {
  AlertingTelemetryPolicy,
  AlertingTelemetryTrigger,
  AlertingTelemetryResult,
  AlertingTelemetryStatistics,
  AlertingTelemetryDiagnostics
} from '../models';

export interface IAlertingTelemetryProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;
  getHealth(): string;
  registerPolicy(policy: AlertingTelemetryPolicy): void;
  unregisterPolicy(policyId: string): void;
  getPolicy(policyId: string): AlertingTelemetryPolicy | null;
  listPolicies(): ReadonlyArray<AlertingTelemetryPolicy>;
  enablePolicy(policyId: string): void;
  disablePolicy(policyId: string): void;
  integrate(trigger: AlertingTelemetryTrigger): Promise<AlertingTelemetryResult>;
  integrateBatch(triggers: ReadonlyArray<AlertingTelemetryTrigger>): Promise<ReadonlyArray<AlertingTelemetryResult>>;
  statistics(): AlertingTelemetryStatistics;
  diagnostics(): AlertingTelemetryDiagnostics;
}
