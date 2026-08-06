/**
 * Configuration Runtime Coordinator Implementation (Phase 16.3.1).
 *
 * Implements IConfigurationRuntime acting as central coordinator for configuration lifecycle
 * operations, delegating directly to IConfigurationProvider.
 */

import {
  ConfigurationDiagnostics,
  ConfigurationHealth,
  ConfigurationState,
  ConfigurationStatistics,
} from './models';
import { IConfigurationProvider, IConfigurationRuntime } from './interfaces';
import { ConfigurationProvider } from './configuration_provider';

export class ConfigurationRuntime implements IConfigurationRuntime {
  private readonly _provider: IConfigurationProvider;

  constructor(provider?: IConfigurationProvider) {
    this._provider = provider ?? new ConfigurationProvider();
  }

  public initialize(): ConfigurationHealth {
    return this._provider.initialize();
  }

  public shutdown(): ConfigurationHealth {
    return this._provider.shutdown();
  }

  public restart(): ConfigurationHealth {
    return this._provider.restart();
  }

  public provider(): IConfigurationProvider {
    return this._provider;
  }

  public health(): ConfigurationHealth {
    return this._provider.health();
  }

  public statistics(): ConfigurationStatistics {
    return this._provider.statistics();
  }

  public diagnostics(): ConfigurationDiagnostics {
    return this._provider.diagnostics();
  }

  public state(): ConfigurationState {
    return this._provider.state();
  }
}
