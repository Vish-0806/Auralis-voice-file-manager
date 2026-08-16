import { ITracingTelemetryProvider } from './tracing-telemetry-provider';

export interface ITracingTelemetryRuntime extends ITracingTelemetryProvider {
  provider(): ITracingTelemetryProvider;
}
