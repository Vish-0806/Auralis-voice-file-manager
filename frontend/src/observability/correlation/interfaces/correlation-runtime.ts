import { ICorrelationProvider } from './correlation-provider';

export interface ICorrelationRuntime extends ICorrelationProvider {
  provider(): ICorrelationProvider;
}
