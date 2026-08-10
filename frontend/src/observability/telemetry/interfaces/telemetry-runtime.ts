import type { ITelemetryProvider } from './telemetry-provider';

export interface ITelemetryRuntime extends ITelemetryProvider {
  provider(): ITelemetryProvider;
}
