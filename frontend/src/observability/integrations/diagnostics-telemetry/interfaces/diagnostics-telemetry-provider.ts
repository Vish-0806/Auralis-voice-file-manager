import {
  DiagnosticsTelemetryPolicy,
  DiagnosticsTelemetryResult,
  DiagnosticsTelemetryStatistics,
  DiagnosticsTelemetryDiagnostics
} from '../models';
import { DiagnosticReport } from '../../../diagnostics/models/report';

export interface IDiagnosticsTelemetryProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;
  getHealth(): string;
  getStatistics(): DiagnosticsTelemetryStatistics;
  getDiagnostics(): DiagnosticsTelemetryDiagnostics;

  registerPolicy(policy: DiagnosticsTelemetryPolicy): void;
  unregisterPolicy(policyId: string): void;
  getPolicy(policyId: string): DiagnosticsTelemetryPolicy | null;
  listPolicies(): ReadonlyArray<DiagnosticsTelemetryPolicy>;
  enablePolicy(policyId: string): void;
  disablePolicy(policyId: string): void;

  processDiagnosticReport(report: DiagnosticReport): Promise<ReadonlyArray<DiagnosticsTelemetryResult>>;
}
