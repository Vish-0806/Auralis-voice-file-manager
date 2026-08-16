import {
  ObservabilityCompositionStateValue,
  ObservabilityCompositionHealth,
  ObservabilityCompositionStatistics,
  ObservabilityCompositionDiagnostics
} from '../models';
import { IMonitoringRuntime } from '../../interfaces/monitoring-runtime';
import { ILoggingRuntime } from '../../logging/interfaces/logging-runtime';
import { IMetricsRuntime } from '../../metrics/interfaces/metrics-runtime';
import { ITracingRuntime } from '../../tracing/interfaces/tracing-runtime';
import { ITelemetryRuntime } from '../../telemetry/interfaces/telemetry-runtime';
import { IDiagnosticsRuntime } from '../../diagnostics/interfaces/diagnostics-runtime';
import { IAlertingRuntime } from '../../alerting/interfaces/alerting-runtime';

export interface IObservabilityCompositionProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): ObservabilityCompositionStateValue;
  getHealth(): ObservabilityCompositionHealth;
  getStatistics(): ObservabilityCompositionStatistics;
  getDiagnostics(): ObservabilityCompositionDiagnostics;

  monitoring(): IMonitoringRuntime;
  logging(): ILoggingRuntime;
  metrics(): IMetricsRuntime;
  tracing(): ITracingRuntime;
  telemetry(): ITelemetryRuntime;
  diagnostics(): IDiagnosticsRuntime;
  alerting(): IAlertingRuntime;
}
