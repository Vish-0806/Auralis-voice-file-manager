import type { ILoggingProvider } from './logging-provider';

export interface ILoggingRuntime extends ILoggingProvider {
  provider(): ILoggingProvider;
}
