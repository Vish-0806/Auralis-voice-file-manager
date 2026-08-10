import type { IMetricsProvider } from './metrics-provider';

export interface IMetricsRuntime extends IMetricsProvider {
  provider(): IMetricsProvider;
}
