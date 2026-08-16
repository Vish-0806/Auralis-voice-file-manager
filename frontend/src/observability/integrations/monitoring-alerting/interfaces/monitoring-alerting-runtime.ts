import { IMonitoringAlertingProvider } from './monitoring-alerting-provider';

export interface IMonitoringAlertingRuntime extends IMonitoringAlertingProvider {
  provider(): IMonitoringAlertingProvider;
}
