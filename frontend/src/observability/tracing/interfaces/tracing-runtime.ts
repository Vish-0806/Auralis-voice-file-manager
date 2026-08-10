import type { ITracingProvider } from './tracing-provider';

export interface ITracingRuntime extends ITracingProvider {
  provider(): ITracingProvider;
}
