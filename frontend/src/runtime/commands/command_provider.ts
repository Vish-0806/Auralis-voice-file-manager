/**
 * Command Provider Implementation (Phase 16.6.1).
 *
 * Implements ICommandProvider owning runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, capabilities
 * reporting, and diagnostics generation for the Frontend Command Runtime.
 */

import {
  CommandCapabilities,
  CommandConfiguration,
  CommandContext,
  CommandDiagnostics,
  CommandHealth,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
  createCommandCapabilities,
  createCommandConfiguration,
  createCommandContext,
  createCommandDiagnostics,
  createCommandHealth,
  createCommandState,
  createCommandStatistics,
} from './models';
import { ICommandProvider } from './interfaces';

export class CommandProvider implements ICommandProvider {
  private _runtimeState: CommandRuntimeState = CommandRuntimeState.UNINITIALIZED;
  private readonly _config: CommandConfiguration;
  private readonly _capabilities: CommandCapabilities;
  private readonly _context: CommandContext;

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: CommandConfiguration,
    capabilities?: CommandCapabilities,
    context?: CommandContext,
  ) {
    this._config = config ?? createCommandConfiguration();
    this._capabilities = capabilities ?? createCommandCapabilities();
    this._context = context ?? createCommandContext();
  }

  public initialize(): CommandHealth {
    if (
      this._runtimeState === CommandRuntimeState.INITIALIZING ||
      this._runtimeState === CommandRuntimeState.READY
    ) {
      return this.health();
    }

    this._runtimeState = CommandRuntimeState.INITIALIZING;
    this._runtimeState = CommandRuntimeState.READY;
    this._startedAt = new Date().toISOString();
    this._initializations++;

    return this.health();
  }

  public shutdown(): CommandHealth {
    if (this._runtimeState === CommandRuntimeState.STOPPED) {
      return this.health();
    }

    this._runtimeState = CommandRuntimeState.STOPPING;
    this._runtimeState = CommandRuntimeState.STOPPED;
    this._startedAt = null;
    this._shutdowns++;

    return this.health();
  }

  public restart(): CommandHealth {
    this._restarts++;
    this.shutdown();
    return this.initialize();
  }

  public health(): CommandHealth {
    const healthy = this._runtimeState === CommandRuntimeState.READY;
    const message = healthy
      ? 'Command runtime is ready and operational.'
      : `Command runtime is in state ${this._runtimeState}.`;

    return createCommandHealth({
      healthy,
      runtimeState: this._runtimeState,
      message,
    });
  }

  public statistics(): CommandStatistics {
    const uptime =
      this._runtimeState === CommandRuntimeState.READY && this._startedAt
        ? Math.max(0, Math.floor((Date.now() - new Date(this._startedAt).getTime()) / 1000))
        : 0;

    return createCommandStatistics({
      initializations: this._initializations,
      shutdowns: this._shutdowns,
      restarts: this._restarts,
      errors: this._errors,
      uptime,
    });
  }

  public capabilities(): CommandCapabilities {
    return this._capabilities;
  }

  public diagnostics(): CommandDiagnostics {
    return createCommandDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      timestamp: new Date().toISOString(),
    });
  }

  public state(): CommandState {
    return createCommandState({
      runtimeState: this._runtimeState,
      initialized: this._runtimeState === CommandRuntimeState.READY,
      startedAt: this._startedAt,
    });
  }

  public configuration(): CommandConfiguration {
    return this._config;
  }

  public context(): CommandContext {
    return this._context;
  }

  public status(): CommandRuntimeState {
    return this._runtimeState;
  }
}
