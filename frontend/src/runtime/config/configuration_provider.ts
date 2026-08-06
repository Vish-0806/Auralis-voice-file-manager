/**
 * Configuration Provider Implementation (Phase 16.3.1).
 *
 * Implements IConfigurationProvider owning configuration runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, and capabilities reporting.
 */

import {
  ConfigurationCapabilities,
  ConfigurationConfiguration,
  ConfigurationContext,
  ConfigurationDiagnostics,
  ConfigurationHealth,
  ConfigurationRuntimeState,
  ConfigurationState,
  ConfigurationStatistics,
  createConfigurationCapabilities,
  createConfigurationConfiguration,
  createConfigurationContext,
  createConfigurationDiagnostics,
  createConfigurationHealth,
  createConfigurationState,
  createConfigurationStatistics,
} from './models';
import { IConfigurationProvider } from './interfaces';

export class ConfigurationProvider implements IConfigurationProvider {
  private _runtimeState: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED;
  private readonly _config: ConfigurationConfiguration;
  private readonly _capabilities: ConfigurationCapabilities;
  private readonly _context: ConfigurationContext;

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: ConfigurationConfiguration,
    capabilities?: ConfigurationCapabilities,
    context?: ConfigurationContext,
  ) {
    this._config = config ?? createConfigurationConfiguration();
    this._capabilities = capabilities ?? createConfigurationCapabilities();
    this._context = context ?? createConfigurationContext();
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
    return createConfigurationDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
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
}
