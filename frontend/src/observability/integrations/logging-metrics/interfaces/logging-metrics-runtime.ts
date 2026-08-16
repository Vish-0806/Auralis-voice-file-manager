import { ILoggingMetricsProvider } from './logging-metrics-provider';

export interface ILoggingMetricsRuntime extends ILoggingMetricsProvider {
  provider(): ILoggingMetricsProvider;
}
