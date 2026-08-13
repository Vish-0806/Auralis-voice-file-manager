import { IDiagnosticsProvider } from './diagnostics-provider';

export interface IDiagnosticsRuntime extends IDiagnosticsProvider {
  provider(): IDiagnosticsProvider;
}
