/**
 * Configuration Provider Implementation (Phase 16.3.2).
 *
 * Implements IConfigurationProvider owning configuration runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, capabilities reporting,
 * and source resolution delegation.
 */

import {
  ConfigurationCapabilities,
  ConfigurationConfiguration,
  ConfigurationContext,
  ConfigurationDiagnostics,
  ConfigurationEntry,
  ConfigurationHealth,
  ConfigurationRuntimeState,
  ConfigurationSnapshot,
  ConfigurationSourceRegistration,
  ConfigurationState,
  ConfigurationStatistics,
  createConfigurationCapabilities,
  createConfigurationConfiguration,
  createConfigurationContext,
  createConfigurationDiagnostics,
  createConfigurationHealth,
  createConfigurationSourceRegistration,
  createConfigurationState,
  createConfigurationStatistics,
} from './models';
import { IConfigurationProvider, IConfigurationSource } from './interfaces';
import { SourceRegistry } from './source_registry';
import { ConfigurationSourceManager } from './configuration_source_manager';
import { MemoryConfigurationSource } from './memory_source';

export class ConfigurationProvider implements IConfigurationProvider {
  private _runtimeState: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED;
  private readonly _config: ConfigurationConfiguration;
  private readonly _capabilities: ConfigurationCapabilities;
  private readonly _context: ConfigurationContext;

  private readonly _registry: SourceRegistry;
  private readonly _sourceManager: ConfigurationSourceManager;
  private readonly _defaultMemorySource: MemoryConfigurationSource;

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: ConfigurationConfiguration,
    capabilities?: ConfigurationCapabilities,
    context?: ConfigurationContext,
    registry?: SourceRegistry,
  ) {
    this._config = config ?? createConfigurationConfiguration();
    this._capabilities = capabilities ?? createConfigurationCapabilities();
    this._context = context ?? createConfigurationContext();

    this._registry = registry ?? new SourceRegistry();
    this._sourceManager = new ConfigurationSourceManager(this._registry);

    this._defaultMemorySource = new MemoryConfigurationSource();
    this._registry.register(this._defaultMemorySource);
  }

  public initialize(): ConfigurationHealth {
    if (
      this._runtimeState === ConfigurationRuntimeState.INITIALIZING ||
      this._runtimeState === ConfigurationRuntimeState.READY
    ) {
      return this.health();
    }

    this._runtimeState = ConfigurationRuntimeState.INITIALIZING;
    this._runtimeState = ConfigurationRuntimeState.READY;
    this._startedAt = new Date().toISOString();
    this._initializations++;

    return this.health();
  }

  public shutdown(): ConfigurationHealth {
    if (this._runtimeState === ConfigurationRuntimeState.STOPPED) {
      return this.health();
    }

    this._runtimeState = ConfigurationRuntimeState.STOPPING;
    this._runtimeState = ConfigurationRuntimeState.STOPPED;
    this._startedAt = null;
    this._shutdowns++;

    return this.health();
  }

  public restart(): ConfigurationHealth {
    this._restarts++;
    this.shutdown();
    return this.initialize();
  }

  public health(): ConfigurationHealth {
    const healthy = this._runtimeState === ConfigurationRuntimeState.READY;
    const message = healthy
      ? 'Configuration runtime is ready and operational.'
      : `Configuration runtime is in state ${this._runtimeState}.`;

    return createConfigurationHealth({
      healthy,
      runtimeState: this._runtimeState,
      message,
    });
  }

  public statistics(): ConfigurationStatistics {
    const uptime =
      this._runtimeState === ConfigurationRuntimeState.READY && this._startedAt
        ? Math.max(0, Math.floor((Date.now() - new Date(this._startedAt).getTime()) / 1000))
        : 0;

    return createConfigurationStatistics({
      initializations: this._initializations,
      shutdowns: this._shutdowns,
      restarts: this._restarts,
      errors: this._errors,
      uptime,
    });
  }

  public capabilities(): ConfigurationCapabilities {
    return this._capabilities;
  }

  public diagnostics(): ConfigurationDiagnostics {
    const sourceRegs: ConfigurationSourceRegistration[] = this.listSources().map((s) =>
      createConfigurationSourceRegistration({
        sourceName: s.name,
        priority: s.priority,
        enabled: s.enabled,
      }),
    );

    return createConfigurationDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      sources: sourceRegs,
      snapshot: this.createSnapshot(),
      timestamp: new Date().toISOString(),
    });
  }

  public state(): ConfigurationState {
    return createConfigurationState({
      runtimeState: this._runtimeState,
      initialized: this._runtimeState === ConfigurationRuntimeState.READY,
      startedAt: this._startedAt,
    });
  }

  public configuration(): ConfigurationConfiguration {
    return this._config;
  }

  public context(): ConfigurationContext {
    return this._context;
  }

  public registerSource(source: IConfigurationSource): void {
    this._registry.register(source);
  }

  public unregisterSource(sourceName: string): boolean {
    return this._registry.unregister(sourceName);
  }

  public get<T = unknown>(key: string, defaultValue?: T): T | undefined {
    return this._sourceManager.get<T>(key, defaultValue);
  }

  public has(key: string): boolean {
    return this._sourceManager.has(key);
  }

  public getEntry(key: string): ConfigurationEntry | undefined {
    return this._sourceManager.getEntry(key);
  }

  public getAll(): Readonly<Record<string, unknown>> {
    return this._sourceManager.getAll();
  }

  public createSnapshot(): ConfigurationSnapshot {
    return this._sourceManager.createSnapshot();
  }

  public listSources(): ReadonlyArray<IConfigurationSource> {
    return this._registry.listSources();
  }
}
