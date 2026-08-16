import {
  LoggingMetricsPolicy,
  LoggingMetricResult,
  LoggingMetricsStatistics,
  LoggingMetricsDiagnostics
} from '../models';
import { LogRecord } from '../../../logging/models/log';

export interface ILoggingMetricsProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;
  getHealth(): string;
  getStatistics(): LoggingMetricsStatistics;
  getDiagnostics(): LoggingMetricsDiagnostics;

  registerPolicy(policy: LoggingMetricsPolicy): void;
  unregisterPolicy(policyId: string): void;
  getPolicy(policyId: string): LoggingMetricsPolicy | null;
  listPolicies(): ReadonlyArray<LoggingMetricsPolicy>;
  enablePolicy(policyId: string): void;
  disablePolicy(policyId: string): void;

  processLogRecord(record: LogRecord): Promise<LoggingMetricResult>;
}
