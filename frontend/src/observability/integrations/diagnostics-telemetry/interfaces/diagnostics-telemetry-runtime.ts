import { IDiagnosticsTelemetryProvider } from './diagnostics-telemetry-provider';

export interface IDiagnosticsTelemetryRuntime extends IDiagnosticsTelemetryProvider {
  provider(): IDiagnosticsTelemetryProvider;
}
