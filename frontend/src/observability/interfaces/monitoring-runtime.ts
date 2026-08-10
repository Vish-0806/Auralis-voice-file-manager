import type { IMonitoringProvider } from './monitoring-provider';

export interface IMonitoringRuntime extends IMonitoringProvider {
  provider(): IMonitoringProvider;
}
