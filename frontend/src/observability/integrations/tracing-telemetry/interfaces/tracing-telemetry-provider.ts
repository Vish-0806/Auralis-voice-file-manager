import {
  TracingTelemetryPolicy,
  TracingTelemetryResult,
  TracingTelemetryStatistics,
  TracingTelemetryDiagnostics
} from '../models';
import { Span } from '../../../tracing/models/span';

export interface ITracingTelemetryProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;
  getHealth(): string;
  getStatistics(): TracingTelemetryStatistics;
  getDiagnostics(): TracingTelemetryDiagnostics;

  registerPolicy(policy: TracingTelemetryPolicy): void;
  unregisterPolicy(policyId: string): void;
  getPolicy(policyId: string): TracingTelemetryPolicy | null;
  listPolicies(): ReadonlyArray<TracingTelemetryPolicy>;
  enablePolicy(policyId: string): void;
  disablePolicy(policyId: string): void;

  processCompletedSpan(span: Span): Promise<TracingTelemetryResult>;
}
