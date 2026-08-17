import { IAlertingTelemetryProvider } from './alerting-telemetry-provider';

export interface IAlertingTelemetryRuntime extends IAlertingTelemetryProvider {
  provider(): IAlertingTelemetryProvider;
}
