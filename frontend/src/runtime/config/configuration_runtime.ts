/**
 * Configuration Runtime Coordinator Implementation (Phase 16.3.2).
 *
 * Implements IConfigurationRuntime acting as central coordinator for configuration lifecycle
 * and source resolution operations, delegating directly to IConfigurationProvider.
 */

import {
  ConfigurationDiagnostics,
  ConfigurationEntry,
  ConfigurationHealth,
  ConfigurationSnapshot,
  ConfigurationState,
  ConfigurationStatistics,
} from './models';
import { IConfigurationProvider, IConfigurationRuntime, IConfigurationSource } from './interfaces';
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

  public registerSource(source: IConfigurationSource): void {
    this._provider.registerSource(source);
  }

  public unregisterSource(sourceName: string): boolean {
    return this._provider.unregisterSource(sourceName);
  }

  public get<T = unknown>(key: string, defaultValue?: T): T | undefined {
    return this._provider.get<T>(key, defaultValue);
  }

  public has(key: string): boolean {
    return this._provider.has(key);
  }

  public getEntry(key: string): ConfigurationEntry | undefined {
    return this._provider.getEntry(key);
  }

  public getAll(): Readonly<Record<string, unknown>> {
    return this._provider.getAll();
  }

  public createSnapshot(): ConfigurationSnapshot {
    return this._provider.createSnapshot();
  }

  public listSources(): ReadonlyArray<IConfigurationSource> {
    return this._provider.listSources();
  }
}
