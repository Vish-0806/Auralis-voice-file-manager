/**
 * Frontend Runtime Coordinator Implementation (Phase 16.1).
 *
 * Runtime coordinator managing lifecycle operations and delegating queries
 * to the underlying IFrontendProvider instance.
 */

import {
  FrontendCapabilities,
  FrontendDiagnostics,
  FrontendHealth,
  FrontendRuntimeState,
  FrontendState,
  FrontendStatistics,
} from './models';
import { IFrontendProvider, IFrontendRuntime } from './interfaces';
import { FrontendProvider } from './frontend_provider';

export class FrontendRuntime implements IFrontendRuntime {
  private readonly _provider: IFrontendProvider;

  constructor(provider?: IFrontendProvider) {
    this._provider = provider ?? new FrontendProvider();
  }

  public initialize(): FrontendHealth {
    return this._provider.initialize();
  }

  public shutdown(): FrontendHealth {
    return this._provider.shutdown();
  }

  public restart(): FrontendHealth {
    return this._provider.restart();
  }

  public health(): FrontendHealth {
    return this._provider.health();
  }

  public statistics(): FrontendStatistics {
    return this._provider.statistics();
  }

  public capabilities(): FrontendCapabilities {
    return this._provider.capabilities();
  }

  public diagnostics(): FrontendDiagnostics {
    return this._provider.diagnostics();
  }

  public status(): FrontendRuntimeState {
    return this._provider.status();
  }

  public state(): FrontendState {
    return this._provider.state();
  }

  public provider(): IFrontendProvider {
    return this._provider;
  }
}
