import { IObservabilityCompositionProvider } from './composition-provider';

export interface IObservabilityCompositionRuntime extends IObservabilityCompositionProvider {
  provider(): IObservabilityCompositionProvider;
}
