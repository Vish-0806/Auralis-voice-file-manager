import { IAlertingProvider } from './alerting-provider';

export interface IAlertingRuntime extends IAlertingProvider {
  provider(): IAlertingProvider;
}